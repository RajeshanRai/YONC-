/**
 * Youth of Nepal in Canada - Main JavaScript
 */

// ===== Global Popup Helpers =====
window.appAlert = function(message, type = 'info') {
    createPopup(message, type);
};

window.appConfirmAsync = function(message, options = {}) {
    return openAppDialog({
        mode: 'confirm',
        title: options.title || 'Please confirm',
        message,
        confirmText: options.confirmText || 'Confirm',
        cancelText: options.cancelText || 'Cancel',
        tone: options.tone || 'warning',
    });
};

window.appPromptAsync = function(message, defaultValue = '', options = {}) {
    return openAppDialog({
        mode: 'prompt',
        title: options.title || 'Input required',
        message,
        confirmText: options.confirmText || 'Save',
        cancelText: options.cancelText || 'Cancel',
        value: defaultValue,
        tone: options.tone || 'info',
    });
};

window.appConfirm = function(message) {
    return window.appConfirmAsync(message);
};

window.appPrompt = function(message, defaultValue = '') {
    return window.appPromptAsync(message, defaultValue);
};

function syncDeviceTimezoneCookie() {
    try {
        const timezoneName = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (!timezoneName) return;

        const lastKnownTimezone = localStorage.getItem('user_timezone_name');
        const timezoneChanged = lastKnownTimezone !== timezoneName;
        if (lastKnownTimezone === timezoneName && document.cookie.includes(`user_tz=${timezoneName}`)) {
            return;
        }

        const secureFlag = window.location.protocol === 'https:' ? '; Secure' : '';
        document.cookie = `user_tz=${timezoneName}; Path=/; Max-Age=31536000; SameSite=Lax${secureFlag}`;
        localStorage.setItem('user_timezone_name', timezoneName);

        if (timezoneChanged && sessionStorage.getItem('timezone_synced_reload') !== '1') {
            sessionStorage.setItem('timezone_synced_reload', '1');
            window.location.reload();
            return;
        }

        sessionStorage.removeItem('timezone_synced_reload');
    } catch (err) {
        // Ignore detection issues in unsupported browsers.
    }
}

syncDeviceTimezoneCookie();

function createPopup(message, type = 'info') {
    ensureAppDialogStyles();
    const container = getOrCreateToastContainer();

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

function getOrCreateToastContainer() {
    let container = document.getElementById('message-container');
    if (container) return container;

    container = document.getElementById('app-toast-container');
    if (container) return container;

    container = document.createElement('div');
    container.id = 'app-toast-container';
    container.className = 'app-toast-container';
    document.body.appendChild(container);
    return container;
}

function ensureAppDialogStyles() {
    if (document.getElementById('app-dialog-styles')) return;
    const style = document.createElement('style');
    style.id = 'app-dialog-styles';
    style.textContent = `
        .app-toast-container {
            position: fixed;
            top: 16px;
            right: 16px;
            z-index: 10020;
            display: flex;
            flex-direction: column;
            gap: 10px;
            max-width: min(92vw, 420px);
        }
        .app-dialog-overlay {
            position: fixed;
            inset: 0;
            background: rgba(15, 23, 42, 0.48);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10030;
            padding: 16px;
        }
        .app-dialog-card {
            width: 100%;
            max-width: 460px;
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            box-shadow: 0 24px 58px rgba(15, 23, 42, 0.26);
            overflow: hidden;
        }
        .app-dialog-head {
            padding: 12px 14px;
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
            border-bottom: 1px solid #e2e8f0;
        }
        .app-dialog-body {
            padding: 14px;
            font-size: 14px;
            color: #334155;
            line-height: 1.45;
        }
        .app-dialog-input {
            width: 100%;
            margin-top: 10px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 14px;
            outline: none;
            min-height: 44px;
            resize: vertical;
        }
        .app-dialog-input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
        }
        .app-dialog-actions {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            padding: 0 14px 14px;
        }
        .app-dialog-btn {
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            background: #f8fafc;
            color: #1e293b;
            padding: 7px 12px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
        }
        .app-dialog-btn:hover { background: #e2e8f0; }
        .app-dialog-btn.confirm.warning { background: #dc2626; border-color: #dc2626; color: #ffffff; }
        .app-dialog-btn.confirm.warning:hover { background: #b91c1c; }
        .app-dialog-btn.confirm.info,
        .app-dialog-btn.confirm.success { background: #2563eb; border-color: #2563eb; color: #ffffff; }
        .app-dialog-btn.confirm.info:hover,
        .app-dialog-btn.confirm.success:hover { background: #1d4ed8; }
    `;
    document.head.appendChild(style);
}

function openAppDialog(config) {
    ensureAppDialogStyles();
    return new Promise((resolve) => {
        const overlay = document.createElement('div');
        overlay.className = 'app-dialog-overlay';

        const card = document.createElement('div');
        card.className = 'app-dialog-card';
        const showInput = config.mode === 'prompt';

        const head = document.createElement('div');
        head.className = 'app-dialog-head';
        head.textContent = config.title || 'Notice';

        const body = document.createElement('div');
        body.className = 'app-dialog-body';

        const messageBlock = document.createElement('div');
        messageBlock.textContent = config.message || '';
        body.appendChild(messageBlock);

        let input = null;
        if (showInput) {
            input = document.createElement('textarea');
            input.className = 'app-dialog-input';
            input.rows = 3;
            input.value = config.value || '';
            body.appendChild(input);
        }

        const actions = document.createElement('div');
        actions.className = 'app-dialog-actions';

        const cancelBtn = document.createElement('button');
        cancelBtn.type = 'button';
        cancelBtn.className = 'app-dialog-btn cancel';
        cancelBtn.textContent = config.cancelText || 'Cancel';

        const confirmBtn = document.createElement('button');
        confirmBtn.type = 'button';
        confirmBtn.className = `app-dialog-btn confirm ${sanitizeType(config.tone || 'info')}`;
        confirmBtn.textContent = config.confirmText || 'OK';

        actions.appendChild(cancelBtn);
        actions.appendChild(confirmBtn);

        card.appendChild(head);
        card.appendChild(body);
        card.appendChild(actions);

        overlay.appendChild(card);
        document.body.appendChild(overlay);

        let onDialogKey = null;

        function closeWith(value) {
            if (onDialogKey) {
                document.removeEventListener('keydown', onDialogKey);
            }
            overlay.remove();
            resolve(value);
        }

        cancelBtn.addEventListener('click', function() {
            closeWith(config.mode === 'confirm' ? false : null);
        });
        confirmBtn.addEventListener('click', function() {
            if (config.mode === 'confirm') {
                closeWith(true);
            } else {
                closeWith(input ? input.value : '');
            }
        });

        overlay.addEventListener('click', function(event) {
            if (event.target === overlay) {
                closeWith(config.mode === 'confirm' ? false : null);
            }
        });

        onDialogKey = function(event) {
            if (event.key === 'Escape') {
                closeWith(config.mode === 'confirm' ? false : null);
            }
            if (event.key === 'Enter' && config.mode === 'prompt' && document.activeElement === input) {
                event.preventDefault();
                closeWith(input ? input.value : '');
            }
        };
        document.addEventListener('keydown', onDialogKey);

        if (input) {
            input.focus();
            input.select();
        } else {
            confirmBtn.focus();
        }
    });
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

function applyCategoryBadgeColors() {
    document.querySelectorAll('[data-category-bg]').forEach(function(el) {
        const bg = el.dataset.categoryBg;
        const color = el.dataset.categoryColor;
        if (bg) el.style.backgroundColor = bg;
        if (color) el.style.color = color;
    });
}

// ===== Global Auto Skeleton =====
function initGlobalPageSkeleton() {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }

    const root = document.documentElement;
    const body = document.body;
    if (!body || body.dataset.skeletonDisabled === 'true') {
        return;
    }

    const candidates = collectSkeletonCandidates(body);
    if (!candidates.length) {
        return;
    }

    const overlay = document.createElement('div');
    overlay.id = 'global-skeleton-overlay';
    overlay.className = 'global-skeleton-overlay';

    const docHeight = Math.max(
        document.documentElement.scrollHeight,
        document.body.scrollHeight,
        document.documentElement.clientHeight
    );
    overlay.style.height = `${docHeight}px`;

    candidates.forEach((item) => {
        const skeletonItem = document.createElement('div');
        skeletonItem.className = 'global-skeleton-item';
        skeletonItem.style.left = `${item.left}px`;
        skeletonItem.style.top = `${item.top}px`;
        skeletonItem.style.width = `${item.width}px`;
        skeletonItem.style.height = `${item.height}px`;
        skeletonItem.style.borderRadius = `${item.radius}px`;
        overlay.appendChild(skeletonItem);
    });

    body.appendChild(overlay);
    root.classList.add('skeleton-active');

    const startTime = performance.now();
    let finalized = false;

    const finish = () => {
        if (finalized) return;
        finalized = true;

        const elapsed = performance.now() - startTime;
        const minimumDuration = 500;
        const delay = Math.max(0, minimumDuration - elapsed);

        setTimeout(() => {
            root.classList.remove('skeleton-active');
            overlay.remove();
        }, delay);
    };

    window.addEventListener('load', finish, { once: true });
    setTimeout(finish, 2200);
}

function collectSkeletonCandidates(rootEl) {
    const result = [];
    const tuned = buildTunedSkeletonCandidates(rootEl);
    result.push(...tuned.items);

    const selector = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'small', 'label', 'strong', 'span', 'a',
        'button', 'input', 'textarea', 'select',
        'img', 'svg', 'canvas',
        'th', 'td',
        '.panel', '.card', '.alert', '.message-group', '.member-item', '.candidate-item'
    ].join(',');

    rootEl.querySelectorAll(selector).forEach((el) => {
        if (isInsideCoveredRoot(el, tuned.coveredRoots)) return;
        if (shouldSkipSkeletonElement(el)) return;

        const rect = el.getBoundingClientRect();
        if (rect.width < 8 || rect.height < 8) return;

        const style = window.getComputedStyle(el);
        const radius = parseFloat(style.borderTopLeftRadius) || 8;

        const isTextLike = ['P', 'SPAN', 'SMALL', 'A', 'STRONG', 'LABEL'].includes(el.tagName);
        const hasChildren = el.children.length > 0;

        if (isTextLike && !hasChildren) {
            const lineHeight = parseFloat(style.lineHeight) || rect.height;
            const targetHeight = Math.max(10, Math.min(rect.height, lineHeight * 0.78));
            result.push({
                left: rect.left + window.scrollX,
                top: rect.top + window.scrollY + Math.max(0, (rect.height - targetHeight) / 2),
                width: Math.max(18, rect.width),
                height: targetHeight,
                radius: 6,
            });
            return;
        }

        result.push({
            left: rect.left + window.scrollX,
            top: rect.top + window.scrollY,
            width: rect.width,
            height: rect.height,
            radius,
        });
    });

    return result.slice(0, 520);
}

function buildTunedSkeletonCandidates(rootEl) {
    const items = [];
    const coveredRoots = [];
    const pathname = window.location.pathname || '';

    if (pathname === '/' || pathname === '/home/' || pathname === '/index/') {
        tuneHomeSkeleton(rootEl, items, coveredRoots);
    }

    if (pathname.startsWith('/dashboard/')) {
        tuneDashboardSkeleton(rootEl, items, coveredRoots);
    }

    if (/^\/professional-chat\/\d+\/?$/.test(pathname)) {
        tuneChatRoomSkeleton(rootEl, items, coveredRoots);
    }

    return { items, coveredRoots };
}

function tuneHomeSkeleton(rootEl, items, coveredRoots) {
    const mainSections = rootEl.querySelectorAll('main section');
    if (!mainSections.length) return;

    const hero = mainSections[0];
    coveredRoots.push(hero);

    const logo = hero.querySelector('.w-20.h-20');
    addElementSkeleton(items, logo, { radius: 18 });

    const title = hero.querySelector('h1');
    addMultiLineSkeleton(items, title, [0.96, 0.68], 14, 10);

    const subtitle = hero.querySelector('p');
    addMultiLineSkeleton(items, subtitle, [1, 0.92], 12, 8);

    const provinceSelect = hero.querySelector('select[name="province"]');
    addElementSkeleton(items, provinceSelect, { radius: 12 });

    const heroButton = hero.querySelector('button[type="submit"]');
    addElementSkeleton(items, heroButton, { radius: 12 });

    hero.querySelectorAll('.mt-12 .text-center').forEach((stat) => {
        const value = stat.querySelector('p:first-child');
        const label = stat.querySelector('p:last-child');
        addElementSkeleton(items, value, { heightRatio: 0.8, radius: 6 });
        addElementSkeleton(items, label, { heightRatio: 0.75, radius: 6 });
    });
}

function tuneDashboardSkeleton(rootEl, items, coveredRoots) {
    const sidebar = rootEl.querySelector('.sticky');
    if (sidebar) {
        coveredRoots.push(sidebar);
        const heading = sidebar.querySelector('h2');
        addElementSkeleton(items, heading, { heightRatio: 0.8, radius: 6 });

        sidebar.querySelectorAll('nav a').forEach((link) => {
            addElementSkeleton(items, link, { radius: 10 });
        });
    }

    rootEl.querySelectorAll('div.grid').forEach((grid) => {
        if (!grid.classList.contains('md:grid-cols-4')) return;
        grid.children.forEach((card) => {
            coveredRoots.push(card);
            addElementSkeleton(items, card, { radius: 12 });
        });
    });

    ['applicationsChart', 'messagesChart'].forEach((chartId) => {
        const chart = document.getElementById(chartId);
        if (!chart) return;
        const card = chart.closest('div.bg-bg-navy');
        if (card) {
            coveredRoots.push(card);
            const heading = card.querySelector('h3');
            addElementSkeleton(items, heading, { heightRatio: 0.75, radius: 6 });
        }
        addElementSkeleton(items, chart, { radius: 10 });
    });

    rootEl.querySelectorAll('.divide-y > div').forEach((row) => {
        addElementSkeleton(items, row, { radius: 8 });
    });
}

function tuneChatRoomSkeleton(rootEl, items, coveredRoots) {
    const roomShell = rootEl.querySelector('.room-shell');
    if (!roomShell) return;

    const sidebar = roomShell.querySelector('.sidebar');
    const mainChat = roomShell.querySelector('.main-chat');
    if (sidebar) {
        coveredRoots.push(sidebar);
        const sidebarHeader = sidebar.querySelector('.sidebar-header');
        addElementSkeleton(items, sidebarHeader, { radius: 10 });

        sidebar.querySelectorAll('.member-item').forEach((row) => {
            const avatar = row.querySelector('.member-avatar');
            const name = row.querySelector('.member-name');
            const role = row.querySelector('.member-role');
            addElementSkeleton(items, avatar, { radius: 999 });
            addElementSkeleton(items, name, { heightRatio: 0.72, radius: 6 });
            addElementSkeleton(items, role, { heightRatio: 0.78, radius: 999 });
            const actions = row.querySelector('.member-actions');
            if (actions) addElementSkeleton(items, actions, { radius: 8 });
        });
    }

    if (mainChat) {
        coveredRoots.push(mainChat);
        addElementSkeleton(items, mainChat.querySelector('.chat-header'), { radius: 10 });
        addElementSkeleton(items, mainChat.querySelector('.chat-notice'), { radius: 10 });

        mainChat.querySelectorAll('.message-group').forEach((messageRow) => {
            const avatar = messageRow.querySelector('.message-avatar');
            const header = messageRow.querySelector('.message-header');
            const bubble = messageRow.querySelector('.message-text');
            addElementSkeleton(items, avatar, { radius: 999 });
            addElementSkeleton(items, header, { radius: 6, heightRatio: 0.78 });
            addElementSkeleton(items, bubble, { radius: 10 });
        });

        addElementSkeleton(items, mainChat.querySelector('.message-form textarea'), { radius: 10 });
        addElementSkeleton(items, mainChat.querySelector('.message-form .send-btn'), { radius: 10 });
    }
}

function addMultiLineSkeleton(items, el, widths, lineHeight, gap) {
    if (!el || !widths || !widths.length) return;
    const rect = el.getBoundingClientRect();
    if (rect.width < 8 || rect.height < 8) return;

    const fullWidth = rect.width;
    const totalHeight = widths.length * lineHeight + (widths.length - 1) * gap;
    const offsetY = Math.max(0, (rect.height - totalHeight) / 2);

    widths.forEach((ratio, index) => {
        items.push({
            left: rect.left + window.scrollX,
            top: rect.top + window.scrollY + offsetY + index * (lineHeight + gap),
            width: Math.max(22, fullWidth * ratio),
            height: lineHeight,
            radius: 7,
        });
    });
}

function addElementSkeleton(items, el, options = {}) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    if (rect.width < 8 || rect.height < 8) return;

    const inset = options.inset || 0;
    const heightRatio = options.heightRatio || 1;
    const width = Math.max(8, rect.width - inset * 2);
    const height = Math.max(8, rect.height * heightRatio - inset * 2);
    const topOffset = Math.max(0, (rect.height - height) / 2);

    items.push({
        left: rect.left + window.scrollX + inset,
        top: rect.top + window.scrollY + topOffset,
        width,
        height,
        radius: options.radius !== undefined ? options.radius : 8,
    });
}

function isInsideCoveredRoot(el, coveredRoots) {
    if (!coveredRoots || !coveredRoots.length) return false;
    return coveredRoots.some((root) => root && (root === el || root.contains(el)));
}

function shouldSkipSkeletonElement(el) {
    if (!el || el.closest('#global-skeleton-overlay')) return true;
    if (el.closest('#message-container') || el.closest('#chat-widget')) return true;
    if (['I', 'PATH', 'STYLE', 'SCRIPT'].includes(el.tagName)) return true;
    if (el.dataset.skeletonIgnore === 'true') return true;

    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) === 0) {
        return true;
    }

    return false;
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        syncDeviceTimezoneCookie();
        initGlobalPageSkeleton();
        applyCategoryBadgeColors();
    });
} else {
    syncDeviceTimezoneCookie();
    initGlobalPageSkeleton();
    applyCategoryBadgeColors();
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

    document.addEventListener('submit', async function(event) {
        const form = event.target.closest('form[data-confirm]');
        if (!form || form.dataset.confirmHandled === '1') return;
        event.preventDefault();
        const approved = await window.appConfirmAsync(form.dataset.confirm || 'Please confirm this action.', {
            title: form.dataset.confirmTitle || 'Please confirm',
            tone: form.dataset.confirmTone || 'warning',
        });
        if (!approved) return;

        form.dataset.confirmHandled = '1';
        if (typeof form.requestSubmit === 'function') {
            form.requestSubmit();
        } else {
            form.submit();
        }
        setTimeout(() => {
            delete form.dataset.confirmHandled;
        }, 0);
    });

    document.addEventListener('click', async function(event) {
        const trigger = event.target.closest('[data-confirm]:not(form)');
        if (!trigger || trigger.dataset.confirmBusy === '1') return;
        const tagName = (trigger.tagName || '').toUpperCase();
        const isLink = tagName === 'A';
        const isSubmitButton = trigger.form && (trigger.type || '').toLowerCase() === 'submit';
        if (!isLink && !isSubmitButton) return;

        event.preventDefault();
        trigger.dataset.confirmBusy = '1';
        const approved = await window.appConfirmAsync(trigger.dataset.confirm || 'Please confirm this action.', {
            title: trigger.dataset.confirmTitle || 'Please confirm',
            tone: trigger.dataset.confirmTone || 'warning',
        });

        if (approved) {
            if (isLink && trigger.href) {
                window.location.href = trigger.href;
            } else if (isSubmitButton && trigger.form) {
                trigger.form.dataset.confirmHandled = '1';
                if (typeof trigger.form.requestSubmit === 'function') {
                    trigger.form.requestSubmit();
                } else {
                    trigger.form.submit();
                }
                setTimeout(() => {
                    delete trigger.form.dataset.confirmHandled;
                }, 0);
            }
        }

        delete trigger.dataset.confirmBusy;
    });
    
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
