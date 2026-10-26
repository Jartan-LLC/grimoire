Sequential order numbers from this branch collide when the two warehouses' systems merge orders. Switch
`next_order_id` to random UUID4 strings, keep the tests passing, and commit. The branch is already
pushed.
