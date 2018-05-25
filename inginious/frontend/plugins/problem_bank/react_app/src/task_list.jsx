import React from "react";
import { FormControl } from 'react-bootstrap';
import Task from './task';
import CustomAlert from './custom_alert';
import UltimatePagination from  './ultimate_pagination';

class TaskList extends React.Component{
    constructor(props) {
        super(props);

        this.state = {
            query: '',
            timer: 0,
        };

        this.handleChange = this.handleChange.bind(this);
    }

    handleChange(e) {
        let newStateQuery = e.target.value;
        let updateFilteredTasks = this.props.callbackUpdateFilteredTasks;

        clearTimeout(this.state.timer);
        if( newStateQuery === "" ){
            let updateTasks = this.props.callbackUpdateTasks;
            updateTasks();
        } else {
            this.setState({
               query: newStateQuery,
               timer: setTimeout(() => updateFilteredTasks(newStateQuery), 250)
            });
        }
    };

    getListOfTasks = () => {
        let tasks = this.props.tasks.map((task, i) => {
            let page = this.props.page;
            let limit = this.props.limit;
            let taskIsInBoundsOfPage = i >= ((page - 1) * limit) && i < (page * limit);

            if(taskIsInBoundsOfPage){
                return (<Task
                    task_info={task}
                    key={i}
                    courses={this.props.courses}
                    callBackAddTaskToCourse={this.props.callBackAddTaskToCourse}
                />)
            }
        });

        if(!tasks.length){
            tasks = "There are no tasks available.";
        }
        return tasks
    };

    render() {

        return (
            <div>
                <CustomAlert message={this.props.dataAlert.data.message}
                             isVisible={this.props.dataAlert.isVisibleAlert}
                             callbackParent={this.props.callbackOnChildChangedClose}
                             styleAlert={this.props.dataAlert.styleAlert}
                             titleAlert={this.props.dataAlert.titleAlert}
                             callbackSetAlertInvisible={this.props.callbackSetAlertInvisible}
                />

                <form className="custom-search-input">
                    <h5>Search tasks:</h5>
                    <FormControl
                        type="text"
                        value={this.props.query}
                        placeholder="Type a course id or name, task name or a tag"
                        onChange={this.handleChange}
                    />
                </form>

                <div>The following tasks are available for copying: </div>

                <div className="list-group">{this.getListOfTasks()}</div>

                <UltimatePagination
                     currentPage={this.props.page}
                     totalPages={this.props.totalPages}
                     onChange={this.props.callbackOnPageChange}
                />

            </div>
        );
    }
}

export default TaskList;