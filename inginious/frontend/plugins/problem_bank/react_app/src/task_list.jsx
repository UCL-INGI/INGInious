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

    render() {
        let tasks = this.props.tasks.map((task, i) => {
            if(i >= ((this.props.page - 1) * this.props.limit) && i < (this.props.page * this.props.limit)){
                return (<Task
                    task_info={task}
                    key={i}
                    courses={this.props.courses}
                    callBackAddTaskToCourse={this.props.callBackAddTaskToCourse}
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

                <CustomAlert message={this.props.dataAlert.data.message}
                             isVisible={this.props.dataAlert.isVisibleAlert}
                             callbackParent={this.props.callbackOnChildChangedClose}
                             styleAlert={this.props.dataAlert.styleAlert}
                             titleAlert={this.props.dataAlert.titleAlert}
                />
            </div>
        );
    }
}

export default TaskList;