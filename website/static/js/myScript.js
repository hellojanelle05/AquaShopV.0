$(".plus-cart").click(function() {
    var id = $(this).attr("pid");
    var quantity = this.parentNode.children[2];

    $.ajax({
        type: "POST",
        url: "/update-cart",
        data: {
            item_id: id,
            action: "plus"
        },
        success: function(data) {
            quantity.innerText = data.quantity;
            document.getElementById(`quantity${id}`).innerText = data.quantity;
        }
    });
});

$(".minus-cart").click(function() {
    var id = $(this).attr("pid");
    var quantity = this.parentNode.children[2];

    $.ajax({
        type: "POST",
        url: "/update-cart",
        data: {
            item_id: id,
            action: "minus"
        },
        success: function(data) {
            if (data.delete) {
                // Remove item
                document.getElementById(`cart-item-${id}`).remove();
                return;
            }

            quantity.innerText = data.quantity;
            document.getElementById(`quantity${id}`).innerText = data.quantity;
        }
    });
});
