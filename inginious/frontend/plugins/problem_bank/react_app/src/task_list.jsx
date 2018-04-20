import React from "react";
import { FormControl } from 'react-bootstrap';
import Task from './task';
import CustomAlert from './custom_alert';
import UltimatePagination from  './ultimate_pagination';

class TaskList extends React.Component{
    constructor(props) {
        super(props);

        this.state = {
            data: {"message" : ""},
            isVisibleAlert: false,
            query: '',
            timer: 0,
        };
        this.onChildChanged = this.onChildChanged.bind(this);
    }

    onChildChanged(courseId, taskId, bankId){
        let addTaskToCourse = this.props.callBackAddTaskToCourse;
        let result = addTaskToCourse(courseId, taskId, bankId);
        result.done((data) => {
            this.setState({
               isVisibleAlert: true,
               data: data
            });
        })
    }

    onChildChangedClose(isVisible){
        this.setState({
           isVisibleAlert: isVisible
        });
    }

    handleChange(e) {
        let newStateQuery = e.target.value;
        let updateFilteredTasks = this.props.callbackUpdateFilteredTasks;

        if( newStateQuery === "" ){
            let updateTasks = this.props.callbackUpdateTasks;
            updateTasks();
        } else {
            clearTimeout(this.state.timer);
            this.setState({
               query: newStateQuery,
               timer: setTimeout(() => updateFilteredTasks(newStateQuery), 250)
            });
        }
    };

    render() {

        let tasks = this.props.tasks.map((task, i) => {
            if(i >= ((this.props.page - 1) * this.props.limit) && i < (this.props.page * this.props.limit)){
                return (<Task
                    task_info={task}
                    key={i}
                    courses={this.props.courses}
                    callBackAddTaskToCourse={this.onChildChanged}
                />)
            }
        });

        return (
            <div>

                <form className="custom-search-input">
                    <h5>Search tasks:</h5>
                    <FormControl
                        type="text"
                        value={this.props.query}
                        placeholder="Search a key word"
                        onChange={(e) => this.handleChange(e)}
                    />
                </form>

                <div>The following tasks are available for copying: </div>

                <div className="list-group">{tasks}</div>

                <UltimatePagination
                     currentPage={this.props.page}
                     totalPages={this.props.totalPages}
                     onChange={this.props.callbackOnPageChange}
                />

                <CustomAlert message={this.state.data["message"]} isVisible={this.state.isVisibleAlert}
                             callbackParent={(isVisible) => this.onChildChangedClose(isVisible)}/>
            </div>
        );
    }
}

export default TaskList;