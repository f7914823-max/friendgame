const tg = window.Telegram.WebApp;
tg.ready();
tg.expand(); // Полноэкранный режим

// Инициализация
tg.MainButton.setText('Сохранить прогресс').show().onClick(saveProgress);

// Загрузка данных из initData (user info)
const user = tg.initDataUnsafe.user;
document.getElementById('username').textContent = user ? `@${user.username || 'Гость'}` : 'Гость';

// Мок-данные (в реале — API к боту или Cloud Storage)
let balance = 1000;
let friends = ['@friend1', '@friend2'];
updateUI();

function updateUI() {
    document.getElementById('balance').textContent = `Баланс: ${balance} 💰`;
    const list = document.getElementById('friends-list');
    list.innerHTML = friends.map(friend => `<li>${friend} <button onclick="inviteFriend('${friend}')">Играть</button></li>`).join('');

    // Адаптация к теме Telegram
    if (tg.colorScheme === 'dark') {
        document.body.style.background = 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)';
    }
}

function addFriend() {
    const username = prompt('Username друга (без @):');
    if (username) {
        friends.push(`@${username}`);
        updateUI();
        tg.showAlert('Друг добавлен!'); // Уведомление в Telegram
        // Отправь запрос боту: tg.sendData(JSON.stringify({action: 'add_friend', username}));
    }
}

function inviteGame() {
    const friend = prompt('Username для приглашения:');
    const desc = prompt('Описание игры:');
    if (friend && desc) {
        tg.showAlert(`Приглашение отправлено @${friend}!`);
        // tg.sendData(JSON.stringify({action: 'invite_game', friend, desc})); // К боту
    }
}

function inviteFriend(friend) {
    tg.showConfirm('Пригласить в игру?', () => {
        document.getElementById('game-area').innerHTML = `Игра с ${friend}! Готов?`;
        balance -= 100; // Ставка
        updateUI();
    });
}

function startGame() {
    tg.showAlert('Игра началась! (Мок — добавь логику)');
    balance += 500; // Выигрыш
    updateUI();
}

function saveProgress() {
    tg.sendData(JSON.stringify({balance, friends})); // Отправка боту для сохранения
    tg.close();
}

// Обработка входящих данных от бота (если нужно)
tg.onEvent('mainButtonClicked', saveProgress);