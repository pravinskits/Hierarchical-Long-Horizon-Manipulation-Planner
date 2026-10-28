package com.example.hierarchicalmanipulationapp.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.example.hierarchicalmanipulationapp.ui.screens.*
import com.example.hierarchicalmanipulationapp.viewmodel.AppViewModelProvider

@Composable
fun AppNavigation(navController: NavHostController, modifier: Modifier = Modifier) {
    NavHost(
        navController = navController,
        startDestination = Screen.Dashboard.route,
        modifier = modifier
    ) {
        composable(Screen.Dashboard.route) {
            DashboardScreen(
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateToCreateTask = { navController.navigate(Screen.CreateTask.route) },
                onNavigateToExperiments = { navController.navigate(Screen.Experiments.route) },
                onNavigateToSettings = { navController.navigate(Screen.Settings.route) }
            )
        }
        
        composable(Screen.CreateTask.route) {
            CreateTaskScreen(
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onTaskCreated = { taskId ->
                    navController.navigate(Screen.Plan.createRoute(taskId)) {
                        popUpTo(Screen.CreateTask.route) { inclusive = true }
                    }
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Plan.route) { backStackEntry ->
            val taskId = backStackEntry.arguments?.getString("taskId") ?: ""
            PlanScreen(
                taskId = taskId,
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateToExecution = { id -> 
                    navController.navigate(Screen.Execution.createRoute(id)) {
                        popUpTo(Screen.Plan.route) { inclusive = true }
                    }
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Execution.route) { backStackEntry ->
            val taskId = backStackEntry.arguments?.getString("taskId") ?: ""
            TaskExecutionScreen(
                taskId = taskId,
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateToDetail = { id -> 
                    navController.navigate(Screen.TaskDetail.createRoute(id)) {
                        popUpTo(Screen.Execution.route) { inclusive = true }
                    }
                },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.TaskDetail.route) { backStackEntry ->
            val taskId = backStackEntry.arguments?.getString("taskId") ?: ""
            TaskDetailScreen(
                taskId = taskId,
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateToFailures = { id -> navController.navigate(Screen.Failure.createRoute(id)) },
                onNavigateToRecovery = { id -> navController.navigate(Screen.Recovery.createRoute(id)) },
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Failure.route) { backStackEntry ->
            val taskId = backStackEntry.arguments?.getString("taskId") ?: ""
            FailureScreen(
                taskId = taskId,
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Recovery.route) { backStackEntry ->
            val taskId = backStackEntry.arguments?.getString("taskId") ?: ""
            RecoveryScreen(
                taskId = taskId,
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Experiments.route) {
            ExperimentsScreen(
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateBack = { navController.popBackStack() }
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                viewModel = viewModel(factory = AppViewModelProvider.Factory),
                onNavigateBack = { navController.popBackStack() }
            )
        }
    }
}
