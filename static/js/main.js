/**
 * Youth of Nepal in Canada - Main JavaScript
 */

// ===== Global Popup Helpers =====
window.appAlert = function(message, type = 'info') {
    createPopup(message, type);
};

window.appConfirm = function(message) {
    return confirm(message);
};

window.appPrompt = function(message, defaultValue = '') {
    return prompt(message, defaultValue);
};

function createPopup(message, type = 'info') {
    const container = document.getElementById('message-container');
    if (!container) {
        alert(message);
        return;
    }

    const popup = document.createElement('div');
    popup.className = `popup-notification popup-${sanitizeType(type)}`;
    popup.innerHTML = `
        <div class="popup-message">${escapeHtml(message)}</div>
        <button class="popup-close" type="button" aria-label="Close">&times;</button>
    `;
    popup.addEventListener('click', function(event) {
        if (event.target.closest('.popup-close')) {
            removePopup(popup);
        }
    });

    container.appendChild(popup);
    setTimeout(() => removePopup(popup), 5200);
}

function removePopup(popup) {
    if (!popup) return;
    popup.style.opacity = '0';
    popup.style.transform = 'translateX(20px)';
    setTimeout(() => popup.remove(), 250);
}

function sanitizeType(type) {
    const normalized = String(type || 'info').trim().split(' ')[0].toLowerCase();
    if (normalized === 'error') return 'danger';
    return ['success', 'info', 'warning', 'danger'].includes(normalized) ? normalized : 'info';
}

// ===== Mobile Menu =====
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

// ===== User Dropdown =====
function toggleUserDropdown() {
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const container = document.getElementById('user-dropdown-container');
    const dropdown = document.getElementById('user-dropdown');
    if (container && dropdown && !container.contains(event.target)) {
        dropdown.classList.add('hidden');
    }
});

// ===== Chat Widget =====
let chatWidgetOpen = false;

function toggleChatWidget() {
    const widget = document.getElementById('chat-widget');
    if (widget) {
        chatWidgetOpen = !chatWidgetOpen;
        widget.classList.toggle('hidden');
        if (chatWidgetOpen) {
            loadConversations();
        }
    }
}

function showConversationList() {
    const listView = document.getElementById('chat-conversation-list');
    const chatView = document.getElementById('chat-messages-area');
    if (listView && chatView) {
        listView.classList.remove('hidden');
        chatView.classList.add('hidden');
    }
}

function showChatView(userId, name, avatar) {
    const listView = document.getElementById('chat-conversation-list');
    const chatView = document.getElementById('chat-messages-area');
    if (listView && chatView) {
        listView.classList.add('hidden');
        chatView.classList.remove('hidden');
        
        document.getElementById('chat-other-name').textContent = name;
        document.getElementById('chat-other-avatar').src = avatar;
        document.getElementById('chat-receiver-id').value = userId;
    }
}

function loadConversations() {
    fetch('/messages/conversations/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateConversationList(data.conversations);
            updateUnreadBadges(data.total_unread);
        }
    })
    .catch(error => console.error('Error loading conversations:', error));
}

function updateConversationList(conversations) {
    const container = document.getElementById('chat-conversation-list');
    if (!container) return;
    
    if (conversations.length === 0) {
        return; // Keep empty state
    }
    
    let html = '';
    conversations.forEach(conv => {
        html += `
            <div onclick="showChatView(${conv.user_id}, '${conv.name}', '${conv.avatar}')" 
                 class="flex items-center gap-3 p-3 rounded-lg hover:bg-bg-navy-hover cursor-pointer transition-colors ${conv.unread > 0 ? 'bg-accent-blue/5' : ''}">
                <div class="relative flex-shrink-0">
                    <img src="${conv.avatar}" alt="" class="w-10 h-10 rounded-full object-cover"
                         onerror="this.src='/static/images/default-avatar.png'">
                    ${conv.unread > 0 ? `<span class="absolute -top-1 -right-1 w-4 h-4 bg-accent-blue rounded-full text-[9px] font-bold text-white flex items-center justify-center">${conv.unread}</span>` : ''}
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-text-primary truncate">${conv.name}</p>
                    <p class="text-xs text-text-muted truncate">${conv.last_message}</p>
                </div>
                <span class="text-[10px] text-text-muted flex-shrink-0">${conv.last_timestamp}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function updateUnreadBadges(count) {
    // Nav badge
    const navBadge = document.getElementById('nav-unread-badge');
    if (navBadge) {
        if (count > 0) {
            navBadge.textContent = count;
            navBadge.classList.remove('hidden');
        } else {
            navBadge.classList.add('hidden');
        }
    }
    
    // Chat badge
    const chatBadge = document.getElementById('chat-unread-badge');
    if (chatBadge) {
        if (count > 0) {
            chatBadge.textContent = count;
            chatBadge.classList.remove('hidden');
        } else {
            chatBadge.classList.add('hidden');
        }
    }
}

function sendChatMessage(event) {
    event.preventDefault();
    const input = document.getElementById('chat-message-input');
    const receiverId = document.getElementById('chat-receiver-id').value;
    const content = input.value.trim();
    
    if (!content || !receiverId) return false;
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');
    
    // Add to UI immediately
    const container = document.getElementById('chat-messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = 'flex justify-end';
    msgDiv.innerHTML = `
        <div class="max-w-[80%] bg-accent-blue text-white rounded-tl-xl rounded-tr-xl rounded-bl-xl px-3 py-2 text-sm">
            ${escapeHtml(content)}
            <p class="text-[10px] text-blue-200 mt-1">Just now</p>
        </div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    
    // Send
    const formData = new FormData();
    formData.append('receiver_id', receiverId);
    formData.append('content', content);
    
    fetch('/messages/send/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            input.value = '';
        }
    })
    .catch(error => console.error('Error sending message:', error));
    
    return false;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== CSRF Token Helper =====
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== Auto-hide Messages =====
document.addEventListener('DOMContentLoaded', function() {
    const messageContainer = document.getElementById('message-container');
    if (messageContainer) {
        setTimeout(() => {
            const alerts = messageContainer.querySelectorAll('.alert');
            alerts.forEach(alert => {
                alert.style.opacity = '0';
                alert.style.transform = 'translateX(100%)';
                setTimeout(() => alert.remove(), 300);
            });
        }, 5000);
    }
    
    // Load unread count on page load
    if (document.getElementById('nav-unread-badge')) {
        fetch('/messages/conversations/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateUnreadBadges(data.total_unread);
            }
        })
        .catch(() => {});
    }
});

// ===== Navbar Scroll Effect =====
let lastScroll = 0;
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('main-navbar');
    if (!navbar) return;
    
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 50) {
        navbar.classList.add('shadow-lg');
    } else {
        navbar.classList.remove('shadow-lg');
    }
    
    lastScroll = currentScroll;
});

// ===== Intersection Observer for Animations =====
const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
};

const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in');
            entry.target.style.opacity = '1';
            fadeInObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.fade-in-on-scroll').forEach(el => {
        el.style.opacity = '0';
        fadeInObserver.observe(el);
    });
});
