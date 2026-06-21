import re
from collections import Counter
from html import escape

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except Exception:  # pragma: no cover - fallback path for missing deps
    TfidfVectorizer = None
    cosine_similarity = None


STOPWORDS = {
    'the', 'and', 'for', 'with', 'you', 'your', 'our', 'from', 'that', 'this', 'will',
    'are', 'was', 'were', 'have', 'has', 'had', 'their', 'they', 'them', 'into', 'about',
    'job', 'role', 'position', 'work', 'team', 'skills', 'skill', 'required', 'experience',
    'years', 'year', 'using', 'use', 'ability', 'including', 'across', 'strong', 'good',
    'is', 'are', 'be', 'been', 'being', 'no', 'not', 'do', 'does', 'did',
}

NOISE_WORDS = {
    'address', 'addresses', 'addressing', 'ad', 'apply', 'applicant', 'application', 'bonus',
    'car', 'cars', 'commute', 'daily', 'dental', 'drug', 'drugs', 'food', 'full-time', 'hour',
    'hours', 'housing', 'insurance', 'location', 'locations', 'pay', 'per', 'salary', 'shift',
    'shifts', 'starting', 'street', 'travel', 'weekend', 'weekends',
    'richmond', 'trucks', 'truck',
    'need', 'needed', 'must',
}

REQUIREMENT_HINTS = (
    'require', 'required', 'preferred', 'must', 'need', 'needed', 'responsible', 'experience',
    'qualification', 'qualifications', 'ability', 'comfortable', 'familiar', 'knowledge',
    'looking for', 'seeking', 'should', 'duties', 'expect', 'expects', 'expecting',
)

SUMMARY_OPENERS = {
    'professional': 'Detail-oriented and reliable candidate with a strong commitment to quality and teamwork',
    'friendly': 'People-focused candidate who enjoys helping teams succeed through communication and care',
    'confident': 'Results-driven candidate with a strong track record of delivering impact in fast-paced environments',
}

ACTION_VERBS = [
    'Delivered', 'Developed', 'Managed', 'Led', 'Designed', 'Implemented',
    'Collaborated', 'Optimized', 'Streamlined', 'Coordinated', 'Supported',
    'Achieved', 'Maintained', 'Established', 'Facilitated', 'Enhanced',
    'Resolved', 'Communicated', 'Executed', 'Contributed', 'Spearheaded',
]


def _normalize_spaces(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').strip())


def _normalize_block(text: str) -> str:
    lines = []
    for raw_line in (text or '').splitlines():
        cleaned = re.sub(r'\s+', ' ', raw_line).strip(' \t-•')
        if cleaned:
            lines.append(cleaned)
    return '\n'.join(lines)


def _split_items(text: str) -> list[str]:
    if not text:
        return []
    chunks = re.split(r'[\n,;|•]+', text)
    result = []
    for chunk in chunks:
        item = _normalize_spaces(chunk)
        if item and item not in result:
            result.append(item)
    return result


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    normalized = _normalize_block(text)
    parts = re.split(r'(?<=[.!?])\s+|\n+', normalized)
    result = []
    for part in parts:
        item = _normalize_spaces(part)
        if item and item not in result:
            result.append(item)
    return result


def _clean_optional_section(text: str) -> str:
    return _normalize_block(text)


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        normalized = _normalize_spaces(item)
        lowered = normalized.lower()
        if normalized and lowered not in seen:
            seen.add(lowered)
            result.append(normalized)
    return result


def _sentence_case(text: str) -> str:
    text = _normalize_spaces(text)
    if not text:
        return text
    return text[0].upper() + text[1:]


def improve_grammar(text: str) -> str:
    """Lightweight grammar cleanup without external services."""
    clean = _sentence_case(text)
    clean = clean.replace(' i ', ' I ')
    clean = re.sub(r'\s+([,.;:!?])', r'\1', clean)
    if clean and clean[-1] not in '.!?':
        clean += '.'
    return clean


def _tokenize(text: str) -> list[str]:
    return re.findall(r'[A-Za-z][A-Za-z+#-]{1,30}', (text or '').lower())


def _looks_like_requirement(sentence: str) -> bool:
    lowered = sentence.lower()
    return any(hint in lowered for hint in REQUIREMENT_HINTS)


def _is_noise_token(token: str) -> bool:
    token = token.lower()
    return token in STOPWORDS or token in NOISE_WORDS or len(token) <= 2


def _phrase_candidates(sentence: str) -> list[str]:
    fragments = re.split(r'(?:[\n,;:/|]+|\band\b|\bor\b|\bbut\b)', sentence, flags=re.IGNORECASE)
    phrases = []

    for fragment in fragments:
        words = _tokenize(fragment)
        current = []

        for word in words:
            if _is_noise_token(word) or word in {'to', 'of', 'in', 'on', 'at', 'by', 'a', 'an', 'the', 'for', 'with', 'from', 'as'}:
                if current:
                    phrases.append(current)
                    current = []
                continue
            current.append(word)

        if current:
            phrases.append(current)

    results = []
    for phrase_words in phrases:
        max_size = min(3, len(phrase_words))
        for size in range(max_size, 0, -1):
            for start in range(0, len(phrase_words) - size + 1):
                candidate = ' '.join(phrase_words[start:start + size]).strip()
                if candidate and candidate not in results:
                    results.append(candidate)
    return results


def _phrase_covers(phrase: str, other: str) -> bool:
    if phrase == other:
        return True
    return re.search(rf'\b{re.escape(other)}\b', phrase) is not None


def extract_keywords(job_description: str, top_k: int = 12) -> list[str]:
    sentences = _split_sentences(job_description)
    requirement_sentences = [sentence for sentence in sentences if _looks_like_requirement(sentence)]
    source_sentences = requirement_sentences or sentences
    if not source_sentences:
        return []

    candidate_counts = Counter()
    candidate_order = {}

    for index, sentence in enumerate(source_sentences):
        for candidate in _phrase_candidates(sentence):
            if any(_is_noise_token(part) for part in candidate.split()):
                continue
            if candidate in {'experience', 'required', 'responsible', 'responsibilities'}:
                continue
            candidate_counts[candidate] += 1
            candidate_order.setdefault(candidate, index)

    ranked_candidates = sorted(
        candidate_counts.items(),
        key=lambda item: (-item[1], -len(item[0].split()), candidate_order.get(item[0], 0), item[0]),
    )
    cleaned = []
    for candidate, _ in ranked_candidates:
        if not candidate:
            continue
        if any(_phrase_covers(existing, candidate) for existing in cleaned):
            continue
        cleaned.append(candidate)
    if cleaned:
        return cleaned[:top_k]

    candidate_text = '\n'.join(source_sentences)
    tokens = [t for t in _tokenize(candidate_text) if not _is_noise_token(t)]
    if tokens:
        return [w for w, _ in Counter(tokens).most_common(top_k)]

    return []


def _match_score(resume_text: str, jd_text: str, keywords: list[str] | None = None) -> float:
    if not resume_text.strip() or not jd_text.strip():
        return 0.0

    resume_lower = resume_text.lower()
    keyword_hits = sum(1 for keyword in (keywords or []) if keyword.lower() in resume_lower)
    keyword_score = (keyword_hits / len(keywords)) if keywords else 0.0

    if TfidfVectorizer is None or cosine_similarity is None:
        jd_tokens = set(_tokenize(jd_text))
        resume_tokens = set(_tokenize(resume_text))
        if not jd_tokens:
            return 0.0
        overlap_score = len(jd_tokens & resume_tokens) / len(jd_tokens)
        return round(min(1.0, (overlap_score * 0.7) + (keyword_score * 0.3)) * 100, 1)

    vec = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=600)
    matrix = vec.fit_transform([resume_text, jd_text])
    score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
    return round(min(1.0, (score * 0.7) + (keyword_score * 0.3)) * 100, 1)


def _build_resume_bullets(experience_text: str, skills: list[str], keywords: list[str], job_title: str, achievements: str) -> list[str]:
    candidates = _split_sentences(experience_text) or _split_items(experience_text)
    bullets = []
    _verb_set = {v.lower() for v in ACTION_VERBS}
    _is_action_start = lambda word: (
        word.lower() in _verb_set
        or bool(re.match(r'[a-z]{3,}(ed|ied)$', word.lower()))  # past-tense verb
        or bool(re.match(r'[a-z]{3,}ing$', word.lower()))         # present-participle
    )

    for idx, item in enumerate(candidates):
        item = re.sub(r'^(I |We |They |He |She )', '', item, flags=re.IGNORECASE)
        item = re.sub(r'^(Responsible for |Duties included |Worked on |Helped with )', '', item, flags=re.IGNORECASE)
        item = _sentence_case(item)
        if not item:
            continue
        first_word = item.split()[0].rstrip('.,') if item.split() else ''
        if not _is_action_start(first_word):
            verb = ACTION_VERBS[idx % len(ACTION_VERBS)]
            item = f'{verb} {item[0].lower()}{item[1:]}'
        item = improve_grammar(item)
        if item and item not in bullets:
            bullets.append(item)

    if skills and keywords:
        kw_str = ', '.join(keywords[:4])
        sk_str = ', '.join(skills[:3])
        bullet = improve_grammar(
            f'Applied expertise in {sk_str} to address key requirements including {kw_str}'
        )
        if bullet not in bullets:
            bullets.append(bullet)
    elif skills:
        bullet = improve_grammar(
            f'Leveraged proficiency in {", ".join(skills[:4])} to support team goals and project delivery'
        )
        if bullet not in bullets:
            bullets.append(bullet)

    achievement_lines = _split_sentences(achievements) or _split_items(achievements)
    for idx, item in enumerate(achievement_lines):
        item = re.sub(r'^(I |We |They )', '', item, flags=re.IGNORECASE)
        item = _sentence_case(item)
        if not item:
            continue
        first_word = item.split()[0].rstrip('.,') if item.split() else ''
        if not _is_action_start(first_word):
            verb = ACTION_VERBS[(len(bullets) + idx) % len(ACTION_VERBS)]
            item = f'{verb} {item[0].lower()}{item[1:]}'
        item = improve_grammar(item)
        if item and item not in bullets:
            bullets.append(item)

    if not bullets:
        role_name = job_title or 'assigned responsibilities'
        bullets = [
            improve_grammar(f'Delivered consistent results across {role_name} through strong work ethic and attention to detail'),
            improve_grammar(f'Collaborated with cross-functional teams to meet project milestones and quality standards'),
        ]

    return _dedupe_preserve_order(bullets)[:6]


def _build_resume_text(full_name: str, email: str, phone: str, location: str, summary: str, skills: list[str], experience_bullets: list[str], education: str, achievements: str, certifications: str, projects: str, languages: str, references: str, additional_information: str) -> str:
    contact_line = ' | '.join([part for part in [email, phone, location] if part])
    sections = [full_name, contact_line, '', 'Professional Summary', summary]

    if skills:
        sections.extend(['', 'Core Competencies', ', '.join(skills)])

    if experience_bullets:
        sections.extend(['', 'Professional Experience'])
        sections.extend(f'- {bullet}' for bullet in experience_bullets)

    if education:
        sections.extend(['', 'Education', education])

    if achievements:
        sections.extend(['', 'Selected Achievements', achievements])

    if certifications:
        sections.extend(['', 'Certifications', certifications])

    if projects:
        sections.extend(['', 'Projects', projects])

    if languages:
        sections.extend(['', 'Languages', languages])

    if references:
        sections.extend(['', 'References', references])

    if additional_information:
        sections.extend(['', 'Additional Information', additional_information])

    return '\n'.join(section for section in sections if section is not None).strip()


def _render_resume_html(full_name: str, contact_line: str, summary: str, skills: list[str], experience_bullets: list[str], education: str, achievements: str, certifications: str, projects: str, languages: str, references: str, additional_information: str) -> str:
    parts = [
        '<div class="resume-preview">',
        '<div class="resume-layout">',
        '<div class="resume-main">',
        f'<h2>{escape(full_name)}</h2>',
        f'<p class="resume-contact"><em>{escape(contact_line)}</em></p>',
    ]

    if summary:
        parts.extend([
            '<h3>Professional Summary</h3>',
            f'<p>{escape(summary)}</p>',
        ])

    if skills:
        parts.append('<h3>Core Competencies</h3>')
        parts.append('<p class="resume-tags">')
        parts.extend(f'<span>{escape(skill)}</span>' for skill in skills)
        parts.append('</p>')

    if experience_bullets:
        parts.append('<h3>Professional Experience</h3>')
        parts.append('<ul>')
        parts.extend(f'<li>{escape(bullet)}</li>' for bullet in experience_bullets)
        parts.append('</ul>')

    if education:
        parts.extend([
            '<h3>Education</h3>',
            f'<p>{escape(education)}</p>',
        ])

    if achievements:
        parts.extend([
            '<h3>Selected Achievements</h3>',
            '<ul class="resume-bullets">',
        ])
        parts.extend(f'<li>{escape(item)}</li>' for item in (_split_sentences(achievements) or _split_items(achievements)))
        parts.append('</ul>')

    parts.append('</div>')

    sidebar_sections = [
        ('Certifications', certifications),
        ('Projects', projects),
        ('Languages', languages),
        ('References', references),
        ('Additional Information', additional_information),
    ]
    sidebar_sections = [(title, content) for title, content in sidebar_sections if content]

    if sidebar_sections:
        parts.append('<aside class="resume-sidebar">')
        for title, content in sidebar_sections:
            parts.append(f'<h3>{escape(title)}</h3>')
            items = _split_sentences(content) or _split_items(content)
            if len(items) > 1:
                parts.append('<ul class="resume-bullets resume-bullets-tight">')
                parts.extend(f'<li>{escape(item)}</li>' for item in items)
                parts.append('</ul>')
            else:
                parts.append(f'<p>{escape(content)}</p>')
        parts.append('</aside>')

    parts.extend(['</div>', '</div>'])
    return ''.join(parts)


def _render_cover_letter_html(cover_letter: str) -> str:
    paragraphs = []
    for paragraph in cover_letter.split('\n\n'):
        clean = _normalize_spaces(paragraph)
        if clean:
            paragraphs.append(f'<p>{escape(clean)}</p>')
    return '<div class="cover-letter-preview">' + ''.join(paragraphs) + '</div>'


def build_resume_and_cover_letter(data: dict) -> dict:
    full_name = _normalize_spaces(data.get('full_name', ''))
    email = _normalize_spaces(data.get('email', ''))
    phone = _normalize_spaces(data.get('phone', ''))
    location = _normalize_spaces(data.get('location', ''))

    education = _normalize_block(data.get('education', ''))
    experience = _normalize_block(data.get('experience_summary', ''))
    achievements = _normalize_block(data.get('achievements', ''))
    skills = _dedupe_preserve_order(_split_items(data.get('skills', '')))
    certifications = _clean_optional_section(data.get('certifications', ''))
    projects = _clean_optional_section(data.get('projects', ''))
    languages = _clean_optional_section(data.get('languages', ''))
    references = _clean_optional_section(data.get('references', ''))
    additional_information = _clean_optional_section(data.get('additional_information', ''))

    job_title = _normalize_spaces(data.get('job_title', ''))
    company_name = _normalize_spaces(data.get('company_name', '')) or 'your organization'
    job_description = _normalize_spaces(data.get('job_description', ''))
    tone = _normalize_spaces(data.get('tone', 'professional')).lower()

    keywords = extract_keywords(job_description)
    relevant_skills = [skill for skill in skills if any(keyword in skill.lower() for keyword in keywords)]
    prioritized_skills = _dedupe_preserve_order(relevant_skills + skills + keywords)[:12]

    role_label = job_title or 'the target role'
    top_skills = ', '.join(prioritized_skills[:4]) if prioritized_skills else 'key competencies'
    tone_openers = {
        'professional': f'Results-driven professional targeting {role_label} positions',
        'friendly': f'Enthusiastic and collaborative professional seeking {role_label} opportunities',
        'confident': f'High-performing professional with a proven track record pursuing {role_label} roles',
    }
    opener = tone_openers.get(tone, tone_openers['professional'])
    summary = improve_grammar(
        f'{opener} with demonstrated expertise in {top_skills}. '
        f'Adept at delivering measurable results through quality-driven execution, '
        f'cross-functional collaboration, and a consistent focus on organizational goals.'
    )

    experience_bullets = _build_resume_bullets(experience, prioritized_skills, keywords, job_title, achievements)
    contact_line = ' | '.join([part for part in [email, phone, location] if part])
    resume_text = _build_resume_text(
        full_name, email, phone, location, summary, prioritized_skills, experience_bullets,
        education, achievements, certifications, projects, languages, references, additional_information,
    )
    resume_html = _render_resume_html(
        full_name, contact_line, summary, prioritized_skills, experience_bullets,
        education, achievements, certifications, projects, languages, references, additional_information,
    )

    intro_line = {
        'professional': f'I am writing to apply for the {job_title} position at {company_name}.',
        'friendly': f'I am excited to apply for the {job_title} role at {company_name}.',
        'confident': f'I am pleased to submit my application for the {job_title} role at {company_name}.',
    }.get(tone, f'I am writing to apply for the {job_title} position at {company_name}.')

    cover_skills = ', '.join(prioritized_skills[:4]) if prioritized_skills else 'customer service, operations, and teamwork'
    cover_keywords = ', '.join(keywords[:5]) if keywords else 'communication, problem solving, and professionalism'
    cover_letter = (
        f'Dear Hiring Team,\n\n'
        f'{intro_line} My application is based on a strong match between my background and the responsibilities described in your posting. '
        f'I bring practical experience in {cover_skills}, along with a work style centered on accountability, reliability, and careful follow-through.\n\n'
        f'Your description highlights priorities such as {cover_keywords}. Across my experience, I have supported similar needs by learning quickly, staying organized under pressure, and communicating clearly with teammates, clients, and supervisors. '
        f'These habits help me contribute steadily and maintain quality in daily work.\n\n'
        f'I would also bring additional value through the wider background reflected in my resume, including education, certifications, projects, references, and other relevant details where applicable. '
        f'I understand that employers value candidates who can adapt, document work clearly, and remain dependable through changing priorities.\n\n'
        f'If selected, I would be ready to contribute from day one while continuing to grow into the role and support long-term team goals. '
        f'Thank you for your time and consideration. I would welcome the opportunity to discuss how my experience can support {company_name}.\n\n'
        f'Sincerely,\n{full_name}'
    )

    match_score = _match_score(resume_text, job_description, keywords)

    return {
        'resume': resume_text,
        'resume_text': resume_text,
        'resume_html': resume_html,
        'resume_payload': {
            'full_name': full_name,
            'contact_line': contact_line,
            'summary': summary,
            'skills': prioritized_skills,
            'experience_bullets': experience_bullets,
            'education': education,
            'achievements': achievements,
            'certifications': certifications,
            'projects': projects,
            'languages': languages,
            'references': references,
            'additional_information': additional_information,
            'keywords': keywords,
            'job_title': job_title,
            'company_name': company_name,
        },
        'cover_letter': cover_letter,
        'cover_letter_text': cover_letter,
        'cover_letter_html': _render_cover_letter_html(cover_letter),
        'cover_payload': {
            'full_name': full_name,
            'company_name': company_name,
            'job_title': job_title,
            'paragraphs': [part for part in cover_letter.split('\n\n') if part.strip()],
            'skills': prioritized_skills,
            'keywords': keywords,
        },
        'keywords': keywords,
        'match_score': match_score,
    }