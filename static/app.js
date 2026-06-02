// Function to load the inventory when the page opens
async function fetchInventory() {
    const response = await fetch('/api/data');
    const data = await response.json();
    
    document.getElementById('booth-status').innerText = data.status;
    
    const grid = document.getElementById('inventory-grid');
    grid.innerHTML = ''; // Clear the grid

    // Loop through the database and create a card for each item
    data.items.forEach(item => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <h2>${item.name}</h2>
            <div class="stock-count" id="stock-${item.id}">${item.stock}</div>
            <button class="sell-btn" onclick="sellItem('${item.id}')">Sell ($${item.price})</button>
        `;
        grid.appendChild(card);
    });
}

// Function triggered when you tap a "Sell" button
async function sellItem(itemId) {
    const response = await fetch('/api/sell', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: itemId })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
        // Instantly update the number on the screen
        document.getElementById(`stock-${itemId}`).innerText = result.remaining;
    } else {
        alert(result.message); // Show an error if you are out of stock
    }
}

// Run the fetch function immediately when the page loads
fetchInventory();
