// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FoodEscrow {
    address public owner;
    uint256 public platformFeeBasisPoints = 100; // 1%

    struct Order {
        address buyer;
        address chef;
        uint256 amount;
        bytes32 deliveryHash; // Hash of the secret for anonymous confirmation
        bool isCompleted;
        bool isDisputed;
    }

    mapping(uint256 => Order) public orders;
    uint256 public orderCount;

    event OrderCreated(uint256 orderId, address buyer, address chef, uint256 amount);
    event OrderCompleted(uint256 orderId);

    constructor() {
        owner = msg.sender;
    }

    function createOrder(address _chef, bytes32 _deliveryHash) external payable {
        require(msg.value > 0, "Amount must be greater than 0");

        orderCount++;
        orders[orderCount] = Order({
            buyer: msg.sender,
            chef: _chef,
            amount: msg.value,
            deliveryHash: _deliveryHash,
            isCompleted: false,
            isDisputed: false
        });

        emit OrderCreated(orderCount, msg.sender, _chef, msg.value);
    }

    function completeOrder(uint256 _orderId, string memory _secret) external {
        Order storage order = orders[_orderId];
        require(!order.isCompleted, "Order already completed");
        require(keccak256(abi.encodePacked(_secret)) == order.deliveryHash, "Invalid secret");

        uint256 fee = (order.amount * platformFeeBasisPoints) / 10000;
        uint256 chefAmount = order.amount - fee;

        order.isCompleted = true;

        payable(owner).transfer(fee);
        payable(order.chef).transfer(chefAmount);

        emit OrderCompleted(_orderId);
    }

    function disputeOrder(uint256 _orderId) external {
        Order storage order = orders[_orderId];
        require(msg.sender == order.buyer || msg.sender == order.chef, "Unauthorized");
        order.isDisputed = true;
    }
}
