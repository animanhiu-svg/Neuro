(function() {
    const tg = window.Telegram.WebApp;
    tg.ready(); tg.expand();

    const user_id = tg.initDataUnsafe.user?.id;
    const chat_id = (user_id && user_id !== 0) ? user_id : 7015403070;

    lucide.createIcons();

    let characters = [];
    try {
        const saved = localStorage.getItem('characters');
        if (saved) characters = JSON.parse(saved);
    } catch(e) {}

    function saveCharacters() {
        localStorage.setItem('characters', JSON.stringify(characters));
    }

    let draft = JSON.parse(localStorage.getItem('character_draft')) || {
        tempId: Date.now(),
        name: '',
        gender: 'male',
        age: '',
        greeting: '',
        appearance: '',
        personality: '',
        scenario: '',
        memory: '',
        tags: '',
        photo: null
    };

    function syncDraft() {
        localStorage.setItem('character_draft', JSON.stringify(draft));
    }

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            syncDraft();
        }
    });

    let pendingCharacterId = null;
    const cropModal = document.getElementById('crop-modal');
    const cropImage = document.getElementById('crop-image');
    const cropCancel = document.getElementById('crop-cancel');
    const cropApply = document.getElementById('crop-apply');
    let cropper = null;
    let pendingFile = null;

    function openCrop(file, charId) {
        const reader = new FileReader();
        reader.onload = (e) => {
            cropImage.src = e.target.result;
            cropModal.classList.add('show');
            if (cropper) cropper.destroy();
            cropper = new Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 1,
                cropBoxMovable: false,
                cropBoxResizable: false,
                toggleDragModeOnDblclick: false,
                background: false,
                modal: false,
                guides: false,
                center: false,
                highlight: false
            });
            pendingFile = file;
            pendingCharacterId = charId;
        };
        reader.readAsDataURL(file);
    }

    cropCancel.addEventListener('click', () => {
        cropModal.classList.remove('show');
        if (cropper) cropper.destroy();
        pendingFile = null;
        pendingCharacterId = null;
    });

    cropApply.addEventListener('click', () => {
        if (!cropper || !pendingFile || pendingCharacterId === null) return;
        const canvas = cropper.getCroppedCanvas({ width: 300, height: 300, imageSmoothingQuality: 'high' });
        const croppedDataUrl = canvas.toDataURL('image/jpeg', 0.9);
        draft.photo = croppedDataUrl;
        syncDraft();
        if (pendingCharacterId !== null) {
            const idx = characters.findIndex(c => c.id === pendingCharacterId);
            if (idx !== -1) {
                characters[idx].photo = croppedDataUrl;
                saveCharacters();
            }
        }
        cropModal.classList.remove('show');
        cropper.destroy();
        pendingFile = null;
        if (document.querySelector('.bar-item.active')?.dataset.tab === 'center') {
            renderCenter(pendingCharacterId);
        }
        pendingCharacterId = null;
    });

    function addMessageToUI(container, text, sender, time, avatarUrl, isResend = false) {
        if (sender === 'user') {
            const div = document.createElement('div');
            div.className = 'message user';
            const msgId = Date.now() + Math.random();
            div.setAttribute('data-msg-id', msgId);
            div.innerHTML = `
                <div class="message-bubble">${escapeHtml(text)}</div>
                <div class="message-time">${time}</div>
                <button class="resend-btn" data-msg-text="${escapeHtml(text)}" style="background: white; border: none; border-radius: 20px; padding: 4px 12px; margin-top: 4px; font-size: 11px; color: #121212; cursor: pointer; font-weight: 500;">↻ Отправить заново</button>
            `;
            container.appendChild(div);
            
            const resendBtn = div.querySelector('.resend-btn');
            resendBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                const originalText = resendBtn.getAttribute('data-msg-text');
                resendBtn.textContent = '⟳ Отправка...';
                resendBtn.disabled = true;
                
                if (window.currentSendMessage) {
                    await window.currentSendMessage(originalText);
                    div.remove();
                }
            });
        } else {
            const div = document.createElement('div');
            div.className = 'message bot';
            div.innerHTML = `
                <div class="message-avatar" style="background-image: url('${avatarUrl || ""}');"></div>
                <div class="message-content">
                    <div class="message-bubble">${escapeHtml(text)}</div>
                    <div class="message-time">${time}</div>
                </div>
            `;
            container.appendChild(div);
        }
        container.scrollTop = container.scrollHeight;
    }

    async function sendMessageToServer(character, text, messagesContainer, storageKey, onReply) {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.innerHTML = '<div class="typing-dots"><span></span><span class="middle"></span><span></span></div>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        let userPromptParts = [];
        userPromptParts.push(`Ты — персонаж с именем ${character.name}. Твоя задача — играть эту роль. Никогда не называй себя другими именами и не будь ассистентом.`);
        if (character.gender) userPromptParts.push(`Твой пол: ${character.gender}.`);
        if (character.age) userPromptParts.push(`Твой возраст: ${character.age}.`);
        if (character.personality) userPromptParts.push(`Твой характер: ${character.personality}.`);
        if (character.scenario) userPromptParts.push(`Сейчас происходит: ${character.scenario}.`);
        const userPrompt = userPromptParts.join('\n');

        const payload = {
            chat_id: chat_id,
            message: text,
            character: {
                nsfw_mode: false,
                user_prompt: userPrompt
            },
            history: []
        };

        try {
            const stored = JSON.parse(localStorage.getItem(storageKey)) || [];
            payload.history = stored.slice(-10).map(msg => ({
                role: msg.sender === 'user' ? 'user' : 'assistant',
                content: msg.text
            }));
        } catch(e) {}

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            const data = await response.json();
            const replyText = data.reply || '🌫️ Тишина...';
            typingDiv.remove();
            const time = new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
            addMessageToUI(messagesContainer, replyText, 'bot', time, character.photo);
            let messages = [];
            try { messages = JSON.parse(localStorage.getItem(storageKey)) || []; } catch(e) {}
            messages.push({ text: replyText, sender: 'bot', time, avatar: character.photo });
            localStorage.setItem(storageKey, JSON.stringify(messages));
            if (onReply) onReply(replyText);
        } catch (err) {
            console.error(err);
            typingDiv.remove();
            const errorMessages = [
                '🌫️ Тишина... персонаж задумался',
                '📡 Сигнал потерян... попробуй ещё раз',
                '🌀 Магия связи дала сбой',
                '🔮 Ничего не пришло из пустоты',
                '⏳ Кажется, персонаж завис в размышлениях'
            ];
            const randomError = errorMessages[Math.floor(Math.random() * errorMessages.length)];
            addMessageToUI(messagesContainer, randomError, 'bot', new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }), character.photo);
        }
    }

    function renderChat(character) {
        const storageKey = `chat_${character.id}`;
        let messages = [];
        try { messages = JSON.parse(localStorage.getItem(storageKey)) || []; } catch(e) {}

        const html = `
            <div class="chat-header">
                <button class="chat-back" id="chat-back"><i data-lucide="arrow-left"></i> Назад</button>
                <div class="chat-avatar" style="background-image: url('${character.photo || ""}');"></div>
                <div class="chat-name">${escapeHtml(character.name)}</div>
            </div>
            <div class="messages" id="chat-messages"></div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="chat-input" placeholder="Написать...">
                <button class="chat-send" id="chat-send"><i data-lucide="send"></i></button>
            </div>
        `;
        contentArea.innerHTML = html;
        lucide.createIcons();

        const messagesContainer = document.getElementById('chat-messages');
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('chat-send');
        const backBtn = document.getElementById('chat-back');

        messages.forEach(msg => {
            addMessageToUI(messagesContainer, msg.text, msg.sender, msg.time, msg.avatar || character.photo);
        });

        function addUserMessage(text) {
            const time = new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' });
            addMessageToUI(messagesContainer, text, 'user', time);
            messages.push({ text, sender: 'user', time });
            localStorage.setItem(storageKey, JSON.stringify(messages));
        }

        async function handleSend(optionalText = null) {
            const text = optionalText !== null ? optionalText : input.value.trim();
            if (!text) return;
            
            if (optionalText === null) {
                addUserMessage(text);
                input.value = '';
            } else {
                addUserMessage(text);
            }
            
            await sendMessageToServer(character, text, messagesContainer, storageKey, (reply) => {
                messages.push({ text: reply, sender: 'bot', time: new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }), avatar: character.photo });
                localStorage.setItem(storageKey, JSON.stringify(messages));
            });
        }

        window.currentSendMessage = handleSend;
        window.currentCharacter = character;
        window.currentStorageKey = storageKey;
        window.currentMessagesContainer = messagesContainer;

        sendBtn.addEventListener('click', () => handleSend());
        input.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSend(); });
        backBtn.addEventListener('click', () => {
            window.currentSendMessage = null;
            renderFeed();
        });
    }

    function renderFeed() {
        if (characters.length === 0) {
            contentArea.innerHTML = `
                <div class="portal-header">
                    <h2>Портал</h2>
                    <p>Создайте своего первого персонажа в центре</p>
                </div>
                <div class="empty-state">✨ Здесь будут ваши персонажи</div>
            `;
            lucide.createIcons();
            return;
        }
        const html = `
            <div class="portal-header">
                <h2>Портал</h2>
                <p>Найди своего героя</p>
            </div>
            <div class="search-box">
                <i data-lucide="search"></i>
                <input type="text" id="searchInput" placeholder="Имя персонажа...">
            </div>
            <div id="charactersList" class="characters-list"></div>
        `;
        contentArea.innerHTML = html;
        lucide.createIcons();

        const searchInput = document.getElementById('searchInput');
        const charactersList = document.getElementById('charactersList');

        function renderCharacters() {
            const query = searchInput.value.toLowerCase();
            let filtered = characters.filter(c => c.name.toLowerCase().includes(query));
            if (filtered.length === 0) {
                charactersList.innerHTML = '<div class="empty-state">✨ Ничего не найдено</div>';
                return;
            }
            charactersList.innerHTML = filtered.map(c => `
                <div class="character-card" data-id="${c.id}">
                    <div class="card-avatar" style="background-image: url('${c.photo || ""}');"></div>
                    <div class="card-info">
                        <div class="card-name">${escapeHtml(c.name)}</div>
                        <div class="card-greeting">${escapeHtml(c.greeting || '')}</div>
                    </div>
                </div>
            `).join('');
            document.querySelectorAll('.character-card').forEach(card => {
                card.addEventListener('click', () => {
                    const id = parseInt(card.dataset.id);
                    const character = characters.find(c => c.id === id);
                    if (character) renderChat(character);
                });
            });
        }

        searchInput.addEventListener('input', renderCharacters);
        renderCharacters();
    }

    function renderChats() {
        if (characters.length === 0) {
            contentArea.innerHTML = `
                <div class="empty-chats">
                    <i data-lucide="message-circle" style="width:48px;height:48px;margin-bottom:16px;"></i>
                    <p>Нет чатов</p>
                    <p style="font-size:12px">Создайте персонажа в центре</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        const chats = characters.map(c => {
            const key = `chat_${c.id}`;
            let lastMessage = "Нет сообщений";
            let lastTime = "";
            try {
                const msgs = JSON.parse(localStorage.getItem(key)) || [];
                if (msgs.length > 0) {
                    const last = msgs[msgs.length-1];
                    lastMessage = last.text;
                    lastTime = last.time;
                }
            } catch(e) {}
            return {
                id: c.id,
                name: c.name,
                avatar: c.photo || "",
                lastMessage: lastMessage,
                lastTime: lastTime
            };
        });
        const html = `
            <div class="chats-list">
                ${chats.map(chat => `
                    <div class="chat-item" data-id="${chat.id}">
                        <div class="chat-item-avatar" style="background-image: url('${chat.avatar}');"></div>
                        <div class="chat-item-info">
                            <div class="chat-item-name">${escapeHtml(chat.name)}</div>
                            <div class="chat-item-last">${escapeHtml(chat.lastMessage)}</div>
                            ${chat.lastTime ? `<div style="font-size:10px; color:#666;">${chat.lastTime}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        contentArea.innerHTML = html;
        lucide.createIcons();
        document.querySelectorAll('.chat-item').forEach(el => {
            const id = parseInt(el.dataset.id);
            const character = characters.find(c => c.id === id);
            if (character) {
                el.addEventListener('click', () => renderChat(character));
            }
        });
    }

    let currentEditId = null;

    function renderCenter(editId = null) {
        currentEditId = editId;
        if (editId !== null) {
            const char = characters.find(c => c.id === editId);
            if (char) {
                draft = { ...draft, ...char };
                syncDraft();
            }
        } else if (!draft.tempId) {
            draft.tempId = Date.now();
            syncDraft();
        }

        const avatarHtml = draft.photo
            ? `<div class="avatar-circle" id="avatar-circle" style="background-image: url('${draft.photo}');"></div>`
            : `<div class="avatar-circle" id="avatar-circle"><i data-lucide="camera" class="camera-icon"></i></div>`;

        const html = `
            <div class="neuro-header"><h1>${editId ? 'РЕДАКТИРОВАТЬ ПЕРСОНАЖА' : 'СОЗДАТЬ ПЕРСОНАЖА'}</h1></div>
            <div class="avatar-block">
                ${avatarHtml}
                <div class="avatar-label" id="upload-label">[ ЗАГРУЗИТЬ ФОТО ]</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ИМЯ ]</div>
                <input type="text" class="input-field" id="name" value="${escapeHtml(draft.name)}" maxlength="30">
                <div class="hint">Как будут звать вашего персонажа?</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ПОЛ ]</div>
                <div class="gender-chips" id="genderChips">
                    <div class="chip ${draft.gender === 'male' ? 'active' : ''}" data-gender="male">М</div>
                    <div class="chip ${draft.gender === 'female' ? 'active' : ''}" data-gender="female">Ж</div>
                    <div class="chip ${draft.gender === 'other' ? 'active' : ''}" data-gender="other">⚥</div>
                </div>
                <div class="hint">Выберите пол для правильных окончаний в речи</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ВОЗРАСТ ]</div>
                <input type="number" class="input-field" id="age" value="${escapeHtml(draft.age)}" min="1" max="120" placeholder="лет">
                <div class="hint">(укажите возраст персонажа)</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ПРИВЕТСТВИЕ ]</div>
                <input type="text" class="input-field" id="greeting" value="${escapeHtml(draft.greeting)}" maxlength="200">
                <div class="char-counter" id="greetingCounter">${draft.greeting.length}/200</div>
                <div class="hint">Первая фраза, которую скажет персонаж при встрече</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ВНЕШНОСТЬ ]</div>
                <textarea class="input-textarea" id="appearance" rows="2" maxlength="500">${escapeHtml(draft.appearance)}</textarea>
                <div class="char-counter" id="appearanceCounter">${draft.appearance.length}/500</div>
                <div class="hint">Волосы, глаза, рост, одежда, особенности внешности</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ХАРАКТЕР / ЛИЧНОСТЬ ]</div>
                <textarea class="input-textarea" id="personality" rows="2" maxlength="500">${escapeHtml(draft.personality)}</textarea>
                <div class="char-counter" id="personalityCounter">${draft.personality.length}/500</div>
                <div class="hint">Черты характера, привычки, манера речи, ценности</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ СЦЕНАРИЙ ]</div>
                <textarea class="input-textarea" id="scenario" rows="2" maxlength="500">${escapeHtml(draft.scenario)}</textarea>
                <div class="char-counter" id="scenarioCounter">${draft.scenario.length}/500</div>
                <div class="hint">Где находится, что происходит, настроение, обстоятельства</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ПАМЯТЬ ]</div>
                <textarea class="input-textarea" id="memory" rows="2" maxlength="500">${escapeHtml(draft.memory)}</textarea>
                <div class="char-counter" id="memoryCounter">${draft.memory.length}/500</div>
                <div class="hint">Важные факты, ключевые события, отношения, секреты</div>
            </div>
            <div class="input-group">
                <div class="input-label">[ ТЕГИ ]</div>
                <input type="text" class="input-field" id="tags" value="${escapeHtml(draft.tags)}" maxlength="100" placeholder="например: киберпанк, магия, детектив">
                <div class="hint">Ключевые слова для поиска</div>
            </div>
            <div class="main-buttons">
                <button class="btn btn-outline" id="resetBtn">СБРОС</button>
                <button class="btn btn-primary" id="activateBtn">${editId ? 'СОХРАНИТЬ' : 'СОЗДАТЬ'}</button>
            </div>
        `;
        contentArea.innerHTML = html;
        lucide.createIcons();

        const nameInput = document.getElementById('name');
        const ageInput = document.getElementById('age');
        const greetingInput = document.getElementById('greeting');
        const appearanceInput = document.getElementById('appearance');
        const personalityInput = document.getElementById('personality');
        const scenarioInput = document.getElementById('scenario');
        const memoryInput = document.getElementById('memory');
        const tagsInput = document.getElementById('tags');
        const genderChips = document.querySelectorAll('.gender-chips .chip');
        const fileInput = document.getElementById('file-input');
        const avatarCircle = document.getElementById('avatar-circle');
        const uploadLabel = document.getElementById('upload-label');
        const resetBtn = document.getElementById('resetBtn');
        const activateBtn = document.getElementById('activateBtn');

        function updateCounters() {
            document.getElementById('greetingCounter').textContent = `${greetingInput.value.length}/200`;
            document.getElementById('appearanceCounter').textContent = `${appearanceInput.value.length}/500`;
            document.getElementById('personalityCounter').textContent = `${personalityInput.value.length}/500`;
            document.getElementById('scenarioCounter').textContent = `${scenarioInput.value.length}/500`;
            document.getElementById('memoryCounter').textContent = `${memoryInput.value.length}/500`;
        }

        nameInput.addEventListener('input', (e) => { draft.name = e.target.value; syncDraft(); });
        ageInput.addEventListener('input', (e) => { draft.age = e.target.value; syncDraft(); });
        greetingInput.addEventListener('input', (e) => { draft.greeting = e.target.value; updateCounters(); syncDraft(); });
        appearanceInput.addEventListener('input', (e) => { draft.appearance = e.target.value; updateCounters(); syncDraft(); });
        personalityInput.addEventListener('input', (e) => { draft.personality = e.target.value; updateCounters(); syncDraft(); });
        scenarioInput.addEventListener('input', (e) => { draft.scenario = e.target.value; updateCounters(); syncDraft(); });
        memoryInput.addEventListener('input', (e) => { draft.memory = e.target.value; updateCounters(); syncDraft(); });
        tagsInput.addEventListener('input', (e) => { draft.tags = e.target.value; syncDraft(); });

        genderChips.forEach(chip => {
            chip.addEventListener('click', () => {
                genderChips.forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                draft.gender = chip.dataset.gender;
                syncDraft();
            });
        });

        function handleFileSelect() {
            if (currentEditId === null && !draft.tempId) {
                draft.tempId = Date.now();
                syncDraft();
                currentEditId = draft.tempId;
                renderCenter(draft.tempId);
                setTimeout(() => {
                    const newAvatarCircle = document.getElementById('avatar-circle');
                    if (newAvatarCircle) newAvatarCircle.click();
                }, 100);
            } else {
                fileInput.click();
            }
        }

        avatarCircle?.addEventListener('click', handleFileSelect);
        uploadLabel?.addEventListener('click', handleFileSelect);

        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const charId = currentEditId !== null ? currentEditId : (draft.tempId || Date.now());
                if (currentEditId === null && !draft.tempId) {
                    draft.tempId = charId;
                    syncDraft();
                    currentEditId = charId;
                    renderCenter(charId);
                }
                openCrop(file, charId);
            }
            fileInput.value = '';
        };

        resetBtn.addEventListener('click', () => {
            if (currentEditId !== null) {
                const idx = characters.findIndex(c => c.id === currentEditId);
                if (idx !== -1) characters.splice(idx, 1);
                saveCharacters();
            }
            draft = {
                tempId: Date.now(),
                name: '',
                gender: 'male',
                age: '',
                greeting: '',
                appearance: '',
                personality: '',
                scenario: '',
                memory: '',
                tags: '',
                photo: null
            };
            syncDraft();
            currentEditId = null;
            renderFeed();
            document.querySelectorAll('.bar-item').forEach(i => i.classList.remove('active'));
            document.querySelector('.bar-item[data-tab="feed"]').classList.add('active');
            tg.HapticFeedback?.impactOccurred('light');
        });

        activateBtn.addEventListener('click', async () => {
            const name = nameInput.value.trim();
            if (!name) {
                tg.showAlert('Введите имя персонажа');
                return;
            }
            const ageVal = ageInput.value.trim();
            if (!ageVal) {
                tg.showAlert('Пожалуйста, укажите возраст');
                return;
            }
            const id = currentEditId !== null ? currentEditId : (draft.tempId || Date.now());
            const updatedData = {
                id: id,
                name: name,
                gender: draft.gender,
                age: ageVal,
                greeting: draft.greeting,
                appearance: draft.appearance,
                personality: draft.personality,
                scenario: draft.scenario,
                memory: draft.memory,
                tags: draft.tags,
                photo: draft.photo
            };
            const idx = characters.findIndex(c => c.id === id);
            if (idx === -1) {
                characters.push(updatedData);
            } else {
                characters[idx] = { ...characters[idx], ...updatedData };
            }
            saveCharacters();
            draft = {
                tempId: Date.now(),
                name: '',
                gender: 'male',
                age: '',
                greeting: '',
                appearance: '',
                personality: '',
                scenario: '',
                memory: '',
                tags: '',
                photo: null
            };
            syncDraft();
            currentEditId = null;
            try {
                await fetch('/save_character', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ chat_id: chat_id, character: updatedData })
                });
            } catch(e) { console.error(e); }
            const chatKey = `chat_${updatedData.id}`;
            if (!localStorage.getItem(chatKey)) {
                localStorage.setItem(chatKey, JSON.stringify([]));
            }
            renderChat(updatedData);
        });
    }

    function renderProfile() {
        const html = `
            <div style="text-align: center; padding: 40px 20px;">
                <i data-lucide="menu" style="width:48px;height:48px;margin-bottom:20px;"></i>
                <p style="margin-bottom: 30px;">НАСТРОЙКИ</p>
                <button id="clearDataBtn" style="background: #ff4d4d; border: none; color: white; padding: 12px 24px; border-radius: 40px; font-weight: bold; font-size: 16px; cursor: pointer; width: 80%;">🗑️ Очистить все данные</button>
                <p style="font-size: 12px; color: #aaa; margin-top: 20px;">Удалятся все персонажи, чаты и фото.</p>
            </div>
        `;
        contentArea.innerHTML = html;
        lucide.createIcons();
        const clearBtn = document.getElementById('clearDataBtn');
        clearBtn.addEventListener('click', () => {
            const keysToKeep = ['tgWebAppData', 'tgWebAppPlatform', 'tgWebAppThemeParams', 'tgWebAppVersion'];
            for (let i = localStorage.length - 1; i >= 0; i--) {
                const key = localStorage.key(i);
                if (key && !keysToKeep.includes(key)) {
                    localStorage.removeItem(key);
                }
            }
            characters = [];
            saveCharacters();
            draft = {
                tempId: Date.now(),
                name: '',
                gender: 'male',
                age: '',
                greeting: '',
                appearance: '',
                personality: '',
                scenario: '',
                memory: '',
                tags: '',
                photo: null
            };
            syncDraft();
            tg.showAlert('Все данные очищены!');
            renderFeed();
            document.querySelectorAll('.bar-item').forEach(i => i.classList.remove('active'));
            document.querySelector('.bar-item[data-tab="feed"]').classList.add('active');
        });
    }

    function renderGames() {
        contentArea.innerHTML = '<div class="placeholder-page"><i data-lucide="layout-grid" style="width:48px;height:48px;margin-bottom:20px;"></i><br>МИНИ-ИГРЫ<br>скоро здесь появятся активности</div>';
        lucide.createIcons();
    }

    const contentArea = document.getElementById('content-area');
    const barItems = document.querySelectorAll('.bar-item');

    barItems.forEach(item => {
        item.addEventListener('click', () => {
            if (document.querySelector('.bar-item.active')?.dataset.tab === 'center') {
                syncDraft();
            }
            barItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            const tab = item.dataset.tab;
            if (tab === 'feed') renderFeed();
            else if (tab === 'chats') renderChats();
            else if (tab === 'center') renderCenter(currentEditId);
            else if (tab === 'games') renderGames();
            else if (tab === 'profile') renderProfile();
            tg.HapticFeedback?.impactOccurred('light');
        });
    });

    const splash = document.getElementById('splash-screen');
    const progressFill = document.getElementById('progress-fill');
    setTimeout(() => progressFill.style.width = '100%', 100);
    setTimeout(() => {
        splash.classList.add('hidden');
        document.getElementById('main-content').classList.add('visible');
        tg.HapticFeedback?.impactOccurred('medium');
    }, 3200);

    renderFeed();
    barItems[0].classList.add('active');

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/[&<>]/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[m]));
    }
})();
