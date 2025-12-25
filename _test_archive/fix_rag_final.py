
"""
This script does three things:
1. Replaces the entire script tag in templates/analysis.html to ensure clean logic for Draggable + AutoHide.
2. Updates the sendQuery function within it to ensure Links open in new tab and Removal of loading message works.
3. Forces a rebuild of the Vector Cache to ensure 'url' field is populated.
"""
import os
import sys

# --- Part 1: Update analysis.html ---
file_path = "templates/analysis.html"

new_script = """<script>
    const container = document.getElementById('ai-assistant-container');
    const fab = document.getElementById('ai-fab');
    const windowEl = document.getElementById('ai-chat-window');
    const closeBtn = document.getElementById('close-chat');
    const messages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');

    // --- 拖动逻辑 ---
    let isDragging = false;
    let hasMoved = false;
    let offset = { x: 0, y: 0 };

    container.addEventListener('mousedown', (e) => {
        isDragging = true;
        hasMoved = false;
        const rect = container.getBoundingClientRect();
        offset.x = e.clientX - rect.left;
        offset.y = e.clientY - rect.top;
        
        container.style.right = 'auto';
        container.style.bottom = 'auto';
        container.style.left = rect.left + 'px';
        container.style.top = rect.top + 'px';
        
        container.style.cursor = 'grabbing';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        hasMoved = true;
        e.preventDefault();
        const x = e.clientX - offset.x;
        const y = e.clientY - offset.y;
        container.style.left = x + 'px';
        container.style.top = y + 'px';
    });

    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            container.style.cursor = 'move';
        }
    });

    // --- 点击与显隐逻辑 ---
    let hideTimer = null;
    let isMouseOver = false;

    fab.addEventListener('click', (e) => {
        if (!hasMoved) {
            windowEl.classList.toggle('d-none');
        }
    });

    closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        windowEl.classList.add('d-none');
    });

    // 鼠标移入: 标记状态，清除定时器
    container.addEventListener('mouseenter', () => {
        isMouseOver = true;
        if (hideTimer) {
            clearTimeout(hideTimer);
            hideTimer = null;
        }
    });

    // 鼠标移出: 标记状态，检查是否需要隐藏
    container.addEventListener('mouseleave', () => {
        isMouseOver = false;
        checkAndHide();
    });
    
    // 输入框失去焦点: 检查是否需要隐藏
    chatInput.addEventListener('blur', () => {
        setTimeout(checkAndHide, 100);
    });

    function checkAndHide() {
        if (isMouseOver || document.activeElement === chatInput) {
            return; 
        }
        if (!windowEl.classList.contains('d-none')) {
            if (hideTimer) clearTimeout(hideTimer);
            hideTimer = setTimeout(() => {
                if (!isMouseOver && document.activeElement !== chatInput) {
                    windowEl.classList.add('d-none');
                }
            }, 3000); 
        }
    }

    function sendQuery() {
        const query = chatInput.value.trim();
        if (!query) return;

        appendMessage('user', query);
        chatInput.value = '';
        
        // 关键点：给 loading 消息一个固定的 class 方便查找
        const loadingId = appendMessage('system', '<div class="spinner-border spinner-border-sm text-primary" role="status"></div> 正在思考中...');

        fetch('/api/rag/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        })
        .then(res => res.json())
        .then(data => {
            // 收到响应后，无论 ID 对不对，强制移除所有“正在思考中”
            removeLoadingMessage();
            
            if (data.error) {
                appendMessage('system', '出错了: ' + data.error);
                return;
            }
            if (data.length === 0) {
                appendMessage('system', '抱歉，没有找到相关电影。');
                return;
            }
            
            let html = '<p class="mb-2 small fw-bold text-primary">为您找到以下电影：</p>';
            data.forEach(m => {
                // 关键点：使用 onclick window.open 打开原始链接
                // 如果 m.url 为空，防止报错，跳转到 #
                const link = m.url ? m.url : '#';
                
                html += `
                <div class="d-flex align-items-start gap-2 mb-2 p-2 border rounded bg-white movie-card-sm" 
                     onclick="window.open('${link}', '_blank')" title="点击查看详情">
                    <img src="${m.pic}" style="width: 40px; height: 56px; object-fit: cover;" class="rounded" referrerpolicy="no-referrer">
                    <div class="flex-grow-1" style="min-width: 0;">
                        <div class="d-flex justify-content-between">
                            <h6 class="mb-0 text-truncate" style="font-size: 0.9rem;">${m.title}</h6>
                            <span class="badge bg-warning text-dark" style="font-size: 0.7rem;">${m.score}</span>
                        </div>
                        <p class="mb-0 text-muted text-truncate small" style="font-size: 0.75rem;">${m.intro}</p>
                        <small class="text-success" style="font-size: 0.65rem;">匹配度: ${(m.similarity * 100).toFixed(0)}%</small>
                    </div>
                </div>`;
            });
            appendMessage('system-rich', html);
        })
        .catch(err => {
            removeLoadingMessage();
            appendMessage('system', '服务器连接失败: ' + err);
        });
    }

    function appendMessage(role, content) {
        const div = document.createElement('div');
        const id = 'msg-' + Date.now() + Math.random().toString(36).substr(2, 5); // Unique ID cache
        div.id = id;
        
        // 标记 loading 消息
        if (content.includes('spinner-border')) {
            div.classList.add('loading-msg');
        }

        if (role === 'user') {
            div.className = "align-self-end bg-primary text-white p-3 rounded-3 shadow-sm";
            div.style.maxWidth = "85%";
            div.innerText = content;
        } else if (role === 'system') {
            div.className = "align-self-start bg-white p-3 rounded-3 shadow-sm border";
            div.style.maxWidth = "85%";
            div.innerHTML = content;
        } else if (role === 'system-rich') {
            div.className = "align-self-start w-100"; 
            div.innerHTML = content;
        }
        
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
        return id;
    }

    // 强力移除 Loading
    function removeLoadingMessage() {
        const loadings = messages.querySelectorAll('.loading-msg');
        loadings.forEach(el => el.remove());
        
        // Fallback for any leftovers
        const spinners = messages.querySelectorAll('.spinner-border');
        spinners.forEach(s => {
             const parent = s.closest('div[id^="msg-"]');
             if (parent) parent.remove();
        });
    }
</script>
"""

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the existing script block (assume it's the last script block)
start_tag = "<script>"
end_tag = "{% endblock %}" # The script is right before endblock

idx_end = content.rfind(end_tag)
if idx_end != -1:
    # Find the last <script> before endblock
    idx_start = content.rfind(start_tag, 0, idx_end)
    if idx_start != -1:
        # Replacement
        final_content = content[:idx_start] + new_script + content[idx_end:]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)
        print("UI Updated.")
    else:
        print("Script tag not found.")
else:
    print("End block not found.")


# --- Part 2: Force Rebuild Cache ---
try:
    print("Rebuilding Vector Cache...")
    sys.path.append(os.getcwd())
    from storage.repository import MovieRepository
    from analysis.vector_service import VectorService
    
    repo = MovieRepository(os.path.join("data", "movie.db"))
    svc = VectorService(repo)
    svc.build_index(force_refresh=True)
    print("Vector Cache Rebuilt.")
except Exception as e:
    print(f"Failed to rebuild cache: {e}")

