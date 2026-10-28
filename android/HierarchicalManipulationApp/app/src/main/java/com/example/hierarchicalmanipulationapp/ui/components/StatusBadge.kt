package com.example.hierarchicalmanipulationapp.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@Composable
fun StatusBadge(status: String, modifier: Modifier = Modifier) {
    val backgroundColor = when (status.uppercase()) {
        "COMPLETED", "SUCCESS", "HEALTHY" -> Color(0xFF4CAF50)
        "RUNNING", "IN_PROGRESS" -> Color(0xFF2196F3)
        "FAILED", "ABORTED", "ERROR" -> MaterialTheme.colorScheme.error
        "PENDING", "CREATED", "PLANNED" -> Color(0xFFFF9800)
        else -> Color.Gray
    }

    Box(
        modifier = modifier
            .background(backgroundColor, RoundedCornerShape(4.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp)
    ) {
        Text(
            text = status.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = Color.White
        )
    }
}
