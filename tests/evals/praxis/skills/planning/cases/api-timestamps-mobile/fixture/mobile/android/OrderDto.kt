package com.acme.shop

data class OrderDto(
    val id: Long,
    val total: Long,
    // Milliseconds since the epoch.
    val created_at: Long,
)
