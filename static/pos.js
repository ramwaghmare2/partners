

    const productList = document.getElementById('product-list').getElementsByTagName('tbody')[0];
    const totalPriceDisplay = document.getElementById('total-price');

    let total = 0;

    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    addToCartButtons.forEach(button => {
        button.addEventListener('click', addProductToCart);
    });

    function addProductToCart(event) {
        const menuItem = event.target.closest('.menu-item');
        const name = menuItem.dataset.name;
        const price = parseFloat(menuItem.dataset.price);
        const item_id = parseInt(menuItem.dataset.id);

        if (isNaN(item_id)) {
            alert("Invalid item ID");
            return;
        }

        const existingProductRow = [...productList.rows].find(row => row.dataset.id === item_id.toString());

        if (existingProductRow) {
            updateQuantity(existingProductRow, 1);
        } else {
            const row = productList.insertRow();
            row.setAttribute('data-id', item_id);

            row.innerHTML = `
                <td>${name}</td>
                <td>₹${price.toFixed(2)}</td>
                <td>
                    <button class="quantity-btn" onclick="updateQuantity(this.closest('tr'), -1)">-</button>
                    <span class="quantity">1</span>
                    <button class="quantity-btn" onclick="updateQuantity(this.closest('tr'), 1)">+</button>
                </td>
                <td class="total-price">₹${price.toFixed(2)}</td>
                <td><button onclick="removeProduct(this, ${item_id})">X</button></td>
            `;

            total += price;
            totalPriceDisplay.textContent = total.toFixed(2);
        }
    }

    function updateQuantity(row, change) {
        const quantityElement = row.querySelector('.quantity');
        let quantity = parseInt(quantityElement.textContent) + change;
        const price = parseFloat(row.cells[1].textContent.replace('₹', ''));
        const totalCell = row.querySelector('.total-price');

        if (quantity <= 0) {
            removeProduct(row.querySelector('button'), row.dataset.id);
            return;
        }

        quantityElement.textContent = quantity;
        totalCell.textContent = `₹${(quantity * price).toFixed(2)}`;

        total += price * change;
        totalPriceDisplay.textContent = total.toFixed(2);
    }

    function removeProduct(button, item_id) {
        const row = button.closest('tr');
        const price = parseFloat(row.cells[1].textContent.replace('₹', ''));
        const quantity = parseInt(row.querySelector('.quantity').textContent);
        const totalForItem = price * quantity;

        total -= totalForItem;
        totalPriceDisplay.textContent = total.toFixed(2);

        row.remove();
    }

    let paymentMethod = '';  

    function selectPayment(method) {
        paymentMethod = method;
        console.log("Selected Payment Method: ", paymentMethod);

        const paymentOptions = document.querySelectorAll('.payment-option');
        paymentOptions.forEach(option => option.classList.remove('selected'));

        const selectedOption = [...paymentOptions].find(option => option.textContent.trim() === method);
        if (selectedOption) selectedOption.classList.add('selected');
    }

    function processOrder() {
        console.log("Order button clicked");

        const kitchenIdElement = document.getElementById('kitchen-id');
        if (!kitchenIdElement) {
            alert("Kitchen ID is missing.");
            return;
        }

        const kitchen_id = kitchenIdElement.value;

        const orderDetails = [];
        if (productList.rows.length === 0) {
            alert('Please add items to the cart before placing an order.');
            return;
        }

        [...productList.rows].forEach(row => {
            const item_id = row.dataset.id;
            const quantity = parseInt(row.querySelector('.quantity').textContent);
            const price = parseFloat(row.cells[1].textContent.replace('₹', ''));

            if (isNaN(item_id)) {
                alert("Invalid item ID in the cart");
                return;
            }

            orderDetails.push({ item_id: item_id, quantity: quantity, price: price });
        });

        if (!paymentMethod) {
            alert('Please select a payment method.');
            return;
        }

        const orderData = {
            kitchen_id: kitchen_id,
            payment_method: paymentMethod,
            cart_items: orderDetails
        };

        fetch('/kitchen/POS-order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderData),
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            if (data.order_id) window.location.href = `/kitchen/POS`;
        })
        .catch(error => {
            alert('An error occurred. Please try again later.');
        });
    }

    function searchItems() {
    let input = document.getElementById("search-bar").value.toLowerCase();
    let menuItems = document.querySelectorAll(".menu-item");

    menuItems.forEach(item => {
        let itemName = item.getAttribute("data-name").toLowerCase();
        if (itemName.includes(input)) {
            item.style.display = "block";
        } else {
            item.style.display = "none";
        }
    });
}