document.addEventListener('click', function(e){
    // Like button toggle (client-only optimistic toggle, stored in localStorage)
    if(e.target && (e.target.classList.contains('btn-like') || e.target.closest('.btn-like'))){
        var btn = e.target.classList.contains('btn-like') ? e.target : e.target.closest('.btn-like');
        var postId = btn.getAttribute('data-post-id');
        var countEl = btn.querySelector('.like-count');
        if(!postId || !countEl) return;
        var csrf = (function(){
            var v=null; var m=document.cookie.match('(^|;)\\s*'+'csrftoken'+'=([^;]+)'); if(m) v=decodeURIComponent(m[2]); return v;
        })();
        // optimistic toggle UI
        var currentlyLiked = btn.getAttribute('data-liked') === '1';
        var newLiked = !currentlyLiked;
        btn.setAttribute('data-liked', newLiked ? '1' : '0');
        btn.setAttribute('aria-pressed', newLiked ? 'true' : 'false');
        btn.classList.toggle('liked', newLiked);
        var count = parseInt(countEl.textContent || '0', 10) || 0;
        countEl.textContent = newLiked ? (count + 1) : Math.max(0, count - 1);
        // send POST to server to persist
        fetch(`/community/post/${postId}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrf,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        }).then(function(res){
            if(!res.ok) throw res;
            return res.json();
        }).then(function(json){
            // update UI from server-authoritative counts
            countEl.textContent = json.likes_count;
            btn.setAttribute('data-liked', json.liked ? '1' : '0');
            btn.setAttribute('aria-pressed', json.liked ? 'true' : 'false');
            btn.classList.toggle('liked', json.liked);
        }).catch(function(err){
            // revert optimistic if request failed
            var revert = !newLiked;
            btn.setAttribute('data-liked', revert ? '1' : '0');
            btn.setAttribute('aria-pressed', revert ? 'true' : 'false');
            btn.classList.toggle('liked', revert);
            // restore displayed count
            countEl.textContent = currentlyLiked ? count : Math.max(0, count - 1);
            if(err && err.status === 403){
                // not authenticated: redirect to login
                window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
            }
        });
    }

    // Toggle top-level comments/replies block when Comment button clicked
    if(e.target && (e.target.classList.contains('btn-comment') || e.target.closest('.btn-comment'))){
        var btn = e.target.classList.contains('btn-comment') ? e.target : e.target.closest('.btn-comment');
        var replies = document.getElementById('replies-block');
        if(!replies) return;

        if(replies.classList.contains('hidden')){
            replies.classList.remove('hidden');
            var ta = replies.querySelector('textarea'); if(ta) ta.focus();
            btn.setAttribute('aria-expanded', 'true');
        } else {
            replies.classList.add('hidden');
            btn.setAttribute('aria-expanded', 'false');
        }
        e.preventDefault();
    }

    // Comment button: scroll to replies
    if(e.target && (e.target.classList.contains('btn-comment') || e.target.closest('.btn-comment'))){
        e.preventDefault();
        var target = document.querySelector('h2'); // Replies heading
        if(target){
            target.scrollIntoView({behavior:'smooth', block:'start'});
        }
    }

    // Share button: use Web Share API if available, fallback to copying URL
    if(e.target && (e.target.classList.contains('btn-share') || e.target.closest('.btn-share'))){
        var loc = window.location.href;
        if(navigator.share){
            navigator.share({title: document.title, url: loc}).catch(function(){});
        } else {
            navigator.clipboard?.writeText(loc).then(function(){
                var btn = e.target.classList.contains('btn-share') ? e.target : e.target.closest('.btn-share');
                var original = btn.textContent;
                btn.textContent = 'Link copied';
                setTimeout(function(){ btn.textContent = original; }, 1400);
            }).catch(function(){
                window.prompt('Copy this link', loc);
            });
        }
    }
});

// On load, mark like button if previously liked
document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('.btn-like[data-post-id]').forEach(function(btn){
        var postId = btn.getAttribute('data-post-id');
        var key = 'post_like_' + postId;
        if(localStorage.getItem(key) === '1'){
            btn.classList.add('liked');
            btn.setAttribute('aria-pressed', 'true');
        }
    });
});
