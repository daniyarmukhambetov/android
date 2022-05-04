package com.example.todo.presenter
import com.example.todo.TODO
import com.example.todo.contract.ContractInterface.*
import com.example.todo.model.MainActivityModel
import com.example.todo.view.Task

class MainActivityPresenter(_view: View): Presenter {
    private var view: View = _view
    private var model: Model = MainActivityModel()
//    init {
//        view.initView()
//    }
    override fun getTODOs(): MutableList<Task> {
        return model.getTODOs()
    }
    override fun getTODO(id: Int): Task {
        return model.getTODO(id)
    }
    override fun createTODO(task: Task) {
        model.createTODO(task)
    }
}