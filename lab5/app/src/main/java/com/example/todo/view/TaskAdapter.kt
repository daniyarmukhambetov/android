package com.example.todo

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.todo.view.Task

class TasksAdapter(private val onClick: (Task) -> Unit) :
    ListAdapter<Task, TasksAdapter.TaskViewHolder>(TaskDiffCallback) {

    /* ViewHolder for Task, takes in the inflated view and the onClick behavior. */
    class TaskViewHolder(itemView: View, val onClick: (Task) -> Unit) :
        RecyclerView.ViewHolder(itemView) {
        private val TaskTitleView: TextView = itemView.findViewById(R.id.task_title)
        private val TaskCompletedView: TextView = itemView.findViewById(R.id.task_completed)
        private var currentTask: Task? = null

        init {
            itemView.setOnClickListener {
                currentTask?.let {
                    onClick(it)
                }
            }
        }

        /* Bind Task name and image. */
        fun bind(Task: Task) {
            currentTask = Task

            TaskCompletedView.text = Task.title
            if (Task.completed) {
                TaskTitleView.text = "DONE!"
            }   else {
                TaskTitleView.text = "TODO!"
            }
        }
    }

    /* Creates and inflates view and return TaskViewHolder. */
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TaskViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.task_item, parent, false)
        return TaskViewHolder(view, onClick)
    }

    /* Gets current Task and uses it to bind view. */
    override fun onBindViewHolder(holder: TaskViewHolder, position: Int) {
        val Task = getItem(position)
        holder.bind(Task)

    }
}


object TaskDiffCallback : DiffUtil.ItemCallback<Task>() {
    override fun areItemsTheSame(oldItem: Task, newItem: Task): Boolean {
        return oldItem == newItem
    }

    override fun areContentsTheSame(oldItem: Task, newItem: Task): Boolean {
        return oldItem.id == newItem.id
    }

}