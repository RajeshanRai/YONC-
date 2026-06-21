import json

from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .ai_engine import build_resume_and_cover_letter
from .exporters import build_docx_bytes, build_pdf_bytes, sanitize_filename
from .forms import ResumeCoverLetterForm


def _format_location(city: str, province: str) -> str:
    city = (city or '').strip()
    province = (province or '').strip()
    if city and province:
        return f'{city}, {province}'
    return city or province


def _build_profile_initial(user):
    initial = {
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'phone': getattr(user, 'phone_number', '') or '',
        'location': _format_location(getattr(user, 'city', ''), getattr(user, 'get_province_display', lambda: '')()),
    }

    user_profile = getattr(user, 'profile', None)
    if user_profile:
        if not initial['location']:
            initial['location'] = _format_location(getattr(user, 'city', ''), getattr(user, 'get_province_display', lambda: '')())
        if getattr(user_profile, 'bio', None):
            initial['experience_summary'] = user_profile.bio
        if getattr(user_profile, 'interests', None):
            initial['achievements'] = user_profile.interests

    expert_profile = getattr(user, 'expert_profile', None)
    if expert_profile:
        initial['phone'] = expert_profile.phone_number or initial['phone']
        initial['location'] = _format_location(expert_profile.city, expert_profile.get_province_display() if hasattr(expert_profile, 'get_province_display') else expert_profile.province)
        if getattr(expert_profile, 'qualifications', None):
            initial['education'] = expert_profile.qualifications
        if getattr(expert_profile, 'bio', None):
            initial['experience_summary'] = expert_profile.bio
        if getattr(expert_profile, 'specialties', None):
            initial['skills'] = expert_profile.specialties

        experiences = getattr(expert_profile, 'experiences', None)
        if experiences is not None:
            experience_lines = []
            for experience in experiences.all():
                description = experience.description.strip() if experience.description else ''
                date_range = experience.get_date_range() if hasattr(experience, 'get_date_range') else ''
                parts = [experience.title, experience.company]
                if date_range:
                    parts.append(date_range)
                if description:
                    parts.append(description)
                experience_lines.append(' | '.join([part for part in parts if part]))
            if experience_lines:
                initial['experience_summary'] = '\n'.join(experience_lines)

    return initial


def tools_home(request):
    tools = [
        {
            'name': 'Resume / Cover Letter Builder',
            'description': 'Generate job-specific resume and cover letter from simple questions with AI-assisted suggestions.',
            'url': reverse('tools:resume_cover_letter_generator'),
            'badge': 'AI + ML',
        },
        {
            'name': 'Interview Practice Simulator',
            'description': 'Practice common interview questions with guided feedback tailored to your target role.',
            'url': reverse('tools:coming_soon'),
            'badge': 'Coming Soon',
        },
        {
            'name': 'Career Path Recommender',
            'description': 'Explore suggested career paths based on your interests, strengths, and preferred industries.',
            'url': reverse('tools:coming_soon'),
            'badge': 'Coming Soon',
        },
        {
            'name': 'Scholarship Finder Assistant',
            'description': 'Find scholarship opportunities and track eligibility requirements in one place.',
            'url': reverse('tools:coming_soon'),
            'badge': 'Coming Soon',
        },
        {
            'name': 'Skill Gap Analyzer',
            'description': 'Compare your current skills against role requirements and get focused improvement tips.',
            'url': reverse('tools:coming_soon'),
            'badge': 'Coming Soon',
        },
        {
            'name': 'Networking Message Builder',
            'description': 'Draft professional outreach messages for mentors, recruiters, and community leaders.',
            'url': reverse('tools:coming_soon'),
            'badge': 'Coming Soon',
        },
    ]

    context = {
        'tools': tools,
        'title': 'Tools',
    }
    return render(request, 'tools/tools_home.html', context)


def resume_cover_letter_generator(request):
    generated = None

    if request.method == 'POST':
        form = ResumeCoverLetterForm(request.POST)
        if form.is_valid():
            generated = build_resume_and_cover_letter(form.cleaned_data)
            generated['resume_payload_json'] = json.dumps(generated.get('resume_payload', {}))
            generated['cover_payload_json'] = json.dumps(generated.get('cover_payload', {}))
    else:
        initial = _build_profile_initial(request.user) if request.user.is_authenticated else {}
        form = ResumeCoverLetterForm(initial=initial)

    context = {
        'form': form,
        'generated': generated,
        'title': 'Resume + Cover Letter Generator',
    }
    return render(request, 'tools/resume_cover_generator.html', context)


def coming_soon(request):
    context = {
        'title': 'Coming Soon',
    }
    return render(request, 'tools/coming_soon.html', context)


@require_POST
def export_generated_document(request):
    document_kind = request.POST.get('document_kind', '').strip().lower()
    export_format = request.POST.get('export_format', '').strip().lower()
    full_name = request.POST.get('full_name', '').strip()

    if document_kind == 'resume':
        body = request.POST.get('resume_text', '')
        payload_raw = request.POST.get('resume_payload', '')
        base_name = f"{sanitize_filename(full_name)}_resume"
    elif document_kind == 'cover_letter':
        body = request.POST.get('cover_text', '')
        payload_raw = request.POST.get('cover_payload', '')
        base_name = f"{sanitize_filename(full_name)}_cover_letter"
    else:
        raise Http404('Unsupported document type.')

    if payload_raw.strip():
        try:
            payload = json.loads(payload_raw)
            if isinstance(payload, dict):
                body = payload
        except Exception:
            pass

    if isinstance(body, str) and not body.strip():
        raise Http404('No content to export.')
    if isinstance(body, dict) and not body:
        raise Http404('No content to export.')

    if export_format == 'docx':
        file_bytes = build_docx_bytes(body)
        response = HttpResponse(
            file_bytes,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        response['Content-Disposition'] = f'attachment; filename="{base_name}.docx"'
        return response

    if export_format == 'pdf':
        file_bytes = build_pdf_bytes(body)
        response = HttpResponse(file_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{base_name}.pdf"'
        return response

    raise Http404('Unsupported export format.')