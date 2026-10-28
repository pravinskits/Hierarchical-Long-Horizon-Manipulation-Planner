package com.example.hierarchicalmanipulationapp.ui.navigation

sealed class Screen(val route: String) {
    object Dashboard : Screen("dashboard")
    object CreateTask : Screen("create_task")
    object Plan : Screen("plan/{taskId}") {
        fun createRoute(taskId: String) = "plan/$taskId"
    }
    object Execution : Screen("execution/{taskId}") {
        fun createRoute(taskId: String) = "execution/$taskId"
    }
    object TaskDetail : Screen("task_detail/{taskId}") {
        fun createRoute(taskId: String) = "task_detail/$taskId"
    }
    object Failure : Screen("failures/{taskId}") {
        fun createRoute(taskId: String) = "failures/$taskId"
    }
    object Recovery : Screen("recovery/{taskId}") {
        fun createRoute(taskId: String) = "recovery/$taskId"
    }
    object Experiments : Screen("experiments")
    object Settings : Screen("settings")
}
