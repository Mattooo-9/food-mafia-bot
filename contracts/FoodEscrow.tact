import "@stdlib/deploy";

message CreateOrder {
    orderId: Int as uint64;
    chef: Address;
}

message CompleteOrder {
    orderId: Int as uint64;
}

message CancelOrder {
    orderId: Int as uint64;
}

struct Order {
    buyer: Address;
    chef: Address;
    amount: Int as coins;
    isCompleted: Bool;
}

contract FoodEscrow with Deployable {
    owner: Address;
    orders: map<Int, Order>;
    platformFee: Int = 1; // 1%

    init() {
        self.owner = sender();
    }

    receive(msg: CreateOrder) {
        let amount: Int = context().value;
        require(amount > 0, "Amount must be greater than 0");

        self.orders.set(msg.orderId, Order{
            buyer: sender(),
            chef: msg.chef,
            amount: amount,
            isCompleted: false
        });
    }

    receive(msg: CompleteOrder) {
        let order: Order? = self.orders.get(msg.orderId);
        require(order != null, "Order not found");
        let unwrappedOrder: Order = order!!;
        require(!unwrappedOrder.isCompleted, "Order already completed");
        require(sender() == unwrappedOrder.buyer, "Only buyer can complete");

        let fee: Int = (unwrappedOrder.amount * self.platformFee) / 100;
        let chefAmount: Int = unwrappedOrder.amount - fee;

        send(SendParameters{
            to: self.owner,
            value: fee,
            mode: SendPayGasSeparately
        });

        send(SendParameters{
            to: unwrappedOrder.chef,
            value: chefAmount,
            mode: SendPayGasSeparately
        });

        unwrappedOrder.isCompleted = true;
        self.orders.set(msg.orderId, unwrappedOrder);
    }

    receive(msg: CancelOrder) {
        let order: Order? = self.orders.get(msg.orderId);
        require(order != null, "Order not found");
        let unwrappedOrder: Order = order!!;
        require(!unwrappedOrder.isCompleted, "Order already completed");
        require(sender() == self.owner, "Only admin can cancel");

        send(SendParameters{
            to: unwrappedOrder.buyer,
            value: unwrappedOrder.amount,
            mode: SendRemainingValue
        });

        self.orders.delete(msg.orderId);
    }

    get fun order(orderId: Int): Order? {
        return self.orders.get(orderId);
    }
}
