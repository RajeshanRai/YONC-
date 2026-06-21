document.addEventListener('click', async function(e){
    // Toggle reply form
    if(e.target && e.target.classList.contains('reply-toggle')){
        e.preventDefault();
        var parent = e.target.closest('.comment-item');
        var form = parent.querySelector('.reply-form');
        if(form.style.display === 'none' || form.style.display === '') form.style.display = 'block'; else form.style.display = 'none';
    }

    // Toggle replies container — lazy load via AJAX on first open
    if(e.target && e.target.classList.contains('view-replies')){
        e.preventDefault();
        var id = e.target.getAttribute('data-id');
        var container = document.querySelector('.replies-container[data-id="'+id+'"]');
        if(!container) return;
        // If not loaded, fetch from server
        if(!container.dataset.loaded){
            fetch(`/community/comments/${id}/replies/`, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
                .then(function(res){ if(!res.ok) throw new Error('Network error'); return res.text(); })
                .then(function(html){
                    container.innerHTML = html;
                    container.dataset.loaded = 'true';
                    container.classList.remove('hidden');
                    e.target.textContent = 'Hide replies';
                }).catch(function(){
                    e.target.textContent = 'Error loading';
                });
        } else {
            if(container.classList.contains('hidden')){
                container.classList.remove('hidden');
                e.target.textContent = 'Hide replies';
            } else {
                container.classList.add('hidden');
                e.target.textContent = 'View ' + (container.querySelectorAll('.comment-item').length) + ' replies';
            }
        }
    }

    // Load more replies (pagination)
    if(e.target && e.target.classList.contains('load-more-replies')){
        e.preventDefault();
        var btn = e.target;
        var next = btn.getAttribute('data-next-page');
        var parentReplies = btn.closest('.replies-container');
        if(!parentReplies || !next) return;
        var parentId = parentReplies.getAttribute('data-id');
        fetch(`/community/comments/${parentId}/replies/?page=${next}`, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(function(res){ if(!res.ok) throw new Error('Network'); return res.text(); })
            .then(function(html){
                parentReplies.innerHTML = html;
            }).catch(function(){ btn.textContent = 'Error'; });
    }

    // Comment edit button: show inline edit form
    if(e.target && e.target.classList.contains('btn-comment-edit')){
        e.preventDefault();
        var id = e.target.getAttribute('data-id');
        var item = document.getElementById('comment-' + id);
        if(!item) return;
        var editForm = item.querySelector('.comment-edit-form');
        if(editForm) editForm.style.display = 'block';
        // hide the comment text while editing
        var ct = item.querySelector('.comment-text'); if(ct) ct.style.display = 'none';
    }

    // Cancel edit
    if(e.target && e.target.classList.contains('btn-cancel-edit')){
        e.preventDefault();
        var formWrap = e.target.closest('.comment-edit-form');
        if(!formWrap) return;
        formWrap.style.display = 'none';
        var item = e.target.closest('.comment-item');
        var ct = item.querySelector('.comment-text'); if(ct) ct.style.display = '';
    }

    // Delete comment
    if(e.target && e.target.classList.contains('btn-comment-delete')){
        e.preventDefault();
        if(!(await window.appConfirmAsync('Delete this comment?', { title: 'Delete comment', tone: 'warning', confirmText: 'Delete' }))) return;
        var id = e.target.getAttribute('data-id');
        var csrf = getCookie('csrftoken');
        fetch(`/community/comment/${id}/delete/`, {
            method: 'POST',
            headers: {'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest'},
            credentials: 'same-origin'
        }).then(function(res){ if(!res.ok) throw res; return res.json(); })
        .then(function(json){
            if(json.success){
                var el = document.getElementById('comment-' + id);
                if(el) el.remove();
            } else {
                window.appAlert('Could not delete comment', 'danger');
            }
        }).catch(function(){ window.appAlert('Network error', 'danger'); });
    }

    // Pin/unpin comment (post owner only)
    if(e.target && e.target.classList.contains('btn-comment-pin')){
        e.preventDefault();
        var id = e.target.getAttribute('data-id');
        var pinned = e.target.getAttribute('data-pinned') === '1';
        var csrf = getCookie('csrftoken');
        fetch(`/community/comment/${id}/pin/`, {
            method: 'POST',
            headers: {'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest', 'Content-Type': 'application/x-www-form-urlencoded'},
            body: 'pin=' + (pinned ? '0' : '1'),
            credentials: 'same-origin'
        }).then(function(res){ if(!res.ok) throw res; return res.json(); })
        .then(function(json){
            if(json.success){
                // reload to reflect pinned order
                window.location.reload();
            } else {
                window.appAlert('Could not pin comment', 'danger');
            }
        }).catch(function(){ window.appAlert('Network error', 'danger'); });
    }
});

// Helper to read CSRF token from cookie
function getCookie(name) {
    var value = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                value = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return value;
}

// AJAX reply submission (handles top-level and per-comment reply forms)
document.addEventListener('submit', function(e){
    var form = e.target.closest && e.target.closest('.ajax-reply-form');
    if(!form) return;
    e.preventDefault();
    var postId = form.getAttribute('data-post-id');
    if(!postId) return;
    var url = `/community/post/${postId}/comment_ajax/`;
    var data = new FormData(form);
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: data,
        credentials: 'same-origin'
    }).then(function(res){ return res.json(); })
    .then(function(json){
        if(json.success){
            var parent_id = json.parent_id;
            var html = json.html;
            if(parent_id){
                // insert into the parent's replies container (if loaded), otherwise load it
                var container = document.querySelector('.replies-container[data-id="'+parent_id+'"]');
                if(container && container.dataset.loaded){
                    // append the new reply
                    container.insertAdjacentHTML('beforeend', html);
                } else if(container){
                    // load replies via fetch to ensure pagination and structure
                    var btn = document.querySelector('.view-replies[data-id="'+parent_id+'"]');
                    if(btn) btn.click();
                }
            } else {
                // top-level: insert into #comments-list
                var list = document.getElementById('comments-list');
                if(list){
                    list.insertAdjacentHTML('afterbegin', html);
                }
            }
            // clear textarea
            var ta = form.querySelector('textarea[name="content"]'); if(ta) ta.value='';
        } else {
            window.appAlert('Could not post reply', 'danger');
        }
    }).catch(function(){ window.appAlert('Network error', 'danger'); });
});

// Handle inline comment edit submissions
document.addEventListener('submit', function(e){
    var form = e.target.closest && e.target.closest('.comment-edit-ajax');
    if(!form) return;
    e.preventDefault();
    var commentId = form.getAttribute('data-comment-id');
    if(!commentId) return;
    var data = new FormData(form);
    fetch(`/community/comment/${commentId}/edit/`, {
        method: 'POST',
        headers: {'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest'},
        body: data,
        credentials: 'same-origin'
    }).then(function(res){ return res.json(); })
    .then(function(json){
        if(json.success){
            // replace the comment HTML with returned html
            var wrapper = document.getElementById('comment-' + commentId);
            if(wrapper && json.html){
                var range = document.createRange();
                var doc = range.createContextualFragment(json.html);
                wrapper.parentNode.replaceChild(doc, wrapper);
            } else {
                // fallback: reload
                window.location.reload();
            }
        } else {
            window.appAlert(json.error || 'Could not save comment', 'danger');
        }
    }).catch(function(){ window.appAlert('Network error', 'danger'); });
});
