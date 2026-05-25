const tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
    manifestUrl: 'https://food-mafia-bot.onrender.com/tonconnect-manifest.json',
    buttonRootId: 'ton-connect'
});

let cart = [];
let total = 0;

const tg = window.Telegram.WebApp;
tg.expand();

document.querySelectorAll('.add-to-cart').forEach(button => {
    button.addEventListener('click', (e) => {
        const item = e.target.closest('.menu-item');
        const id = item.dataset.id;
        const price = parseFloat(item.dataset.price);

        cart.push({ id, price });
        total += price;

        updateUI();
    });
});

function updateUI() {
    document.getElementById('total-price').innerText = total.toFixed(2);
    const checkoutBtn = document.getElementById('checkout-btn');
    checkoutBtn.disabled = cart.length === 0 || !tonConnectUI.connected;
}

tonConnectUI.onStatusChange(wallet => {
    updateUI();
});

document.getElementById('checkout-btn').addEventListener('click', async () => {
    if (!tonConnectUI.connected) {
        alert('Please connect your wallet first!');
        return;
    }

    const orderId = Math.floor(Math.random() * 1000000);
    const amountInNanotons = (total * 1000000000).toString();

    // In a real app, this address would be your deployed FoodEscrow contract
    const contractAddress = "EQD__________________________________________";

    const transaction = {
        validUntil: Math.floor(Date.now() / 1000) + 60,
        messages: [
            {
                address: contractAddress,
                amount: amountInNanotons,
                // Payload would be the BOC of CreateOrder message
                payload: "te6ccgEBAQEAAgAAAA=="
            }
        ]
    };

    try {
        const result = await tonConnectUI.sendTransaction(transaction);
        tg.showAlert(`Order #${orderId} placed! Transaction sent.`);
        cart = [];
        total = 0;
        updateUI();
    } catch (e) {
        console.error(e);
        tg.showAlert('Transaction failed or cancelled.');
    }
});
