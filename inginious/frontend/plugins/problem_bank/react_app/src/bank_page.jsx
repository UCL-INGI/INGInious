import React from 'react';
import { Tabs, Tab } from 'react-bootstrap';
import BankCourseList from './bank_course_list';
import TaskList from './task_list';
/*global $:false*/

class BankPage extends React.Component {

     constructor(props) {
        super(props);

        this.state = {
            tasks: [],
            courses: [],
            availableCourses: [],
            availableCoursesToCopy: [],
            pageTasks: 1,
            pageCourses: 1,
            pageAvailableCourses:1,
            totalPagesTasks: 1,
            totalPagesCourses: 1,
            totalPagesAvailableCourses: 1,
            dataAlertCourseList: {
                data: {"message" : ""},
                isVisibleAlert: false,
                titleAlert: '',
                styleAlert: ''
            },
            dataAlertTaskList: {
                data: {"message" : ""},
                isVisibleAlert: false,
                titleAlert: '',
                styleAlert: ''
            }
        };

        this.limit = 10;

        this.onPageTaskChange = this.onPageTaskChange.bind(this);
        this.onPageCourseChange = this.onPageCourseChange.bind(this);
        this.addTaskToCourse = this.addTaskToCourse.bind(this);

        this.updateBankCoursesAsync = this.updateBankCoursesAsync.bind(this);
        this.updateTasksAsync = this.updateTasksAsync.bind(this);
        this.updateAvailableCoursesAsync = this.updateAvailableCoursesAsync.bind(this);
        this.updateAvailableCoursesToCopyAsync = this.updateAvailableCoursesToCopyAsync.bind(this);

        this.deleteCourse = this.deleteCourse.bind(this);
        this.updateFilteredTasksAsync = this.updateFilteredTasksAsync.bind(this);
        this.addCourse = this.addCourse.bind(this);

        this.onAlertTaskListClose = this.onAlertTaskListClose.bind(this);
        this.onAlertCourseListClose = this.onAlertCourseListClose.bind(this);
        this.setAlertCourseListInvisible = this.setAlertCourseListInvisible.bind(this);
        this.setAlertTaskListInvisible = this.setAlertTaskListInvisible.bind(this);

        this.onPageTaskChange = this.onPageTaskChange.bind(this);
        this.onPageCourseChange = this.onPageCourseChange.bind(this);
        this.onPageAvailableCourseChange = this.onPageAvailableCourseChange.bind(this);
    }

    updateBankCoursesAsync() {
        $.getJSON("/plugins/problems_bank/api/bank_courses").then((courses) => {
            let newCourses = courses;
            let newTotalPages = Math.ceil(newCourses.length / this.limit);
            if(newTotalPages === 0){
                newTotalPages = 1;
            }
            this.setState({
                totalPagesCourses: newTotalPages,
                pageCourses: 1,
                courses: newCourses
            })
        });
    }

    updateTasksAsync() {
        $.getJSON("/plugins/problems_bank/api/bank_tasks").then((tasks) => {
            let newTasksLength = tasks.length;
            let newTotalPages = Math.ceil(newTasksLength / this.limit);
            if(newTotalPages === 0){
                newTotalPages = 1;
            }

            this.setState({
                totalPagesTasks: newTotalPages,
                pageTasks: 1,
                tasks,
            });
        });
    }

    updateAvailableCoursesAsync() {
        $.getJSON("/plugins/problems_bank/api/available_courses").then((availableCourses) => {
            let newCourses = availableCourses;
            let newTotalPages = Math.ceil(newCourses.length / this.limit);
            if(newTotalPages === 0){
                newTotalPages = 1;
            }
            this.setState({
                totalPagesAvailableCourses: newTotalPages,
                pageAvailableCourses: 1,
                availableCourses: availableCourses
            });
        });
    }

    updateAvailableCoursesToCopyAsync() {
        $.getJSON("/plugins/problems_bank/api/available_courses_to_copy").then((availableCoursesToCopy) => {
            this.setState({
                availableCoursesToCopy: availableCoursesToCopy
            });
        });
    }

    deleteCourse(course_id){
        $.ajax({
            url: '/plugins/problems_bank/api/bank_courses?' + $.param({"course_id": course_id}),
            type: "DELETE",
            success: (data) => {
                this.updateBankCoursesAsync();
                this.updateAvailableCoursesAsync();
                this.updateTasksAsync();
            }
        }).done((data) => {
            this.setState( {
                dataAlertCourseList:{
                    data: data,
                    isVisibleAlert: true,
                    titleAlert: "Success!",
                    styleAlert: "success"
                }
            });
        }).error((data) => {
            this.setState( {
                dataAlertCourseList: {
                    isVisibleAlert: true,
                    data: {"message": data["responseJSON"]["error"]},
                    titleAlert: "Error!",
                    styleAlert: "danger"
                }
            });
        });
    };

    updateFilteredTasksAsync(query){
        $.post( "/plugins/problems_bank/api/filter_bank_tasks", { "task_query": query }, (filteredTasks) => {
            let newTotalPages = Math.ceil(filteredTasks.length / this.limit);
            let newPage = this.state.pageTasks;
            if( newTotalPages >= 1) {
                if( this.state.pageTasks > newTotalPages){
                    newPage = newTotalPages
                }
            } else {
                newPage = 1;
                newTotalPages = 1;
            }

            this.setState({
                tasks : filteredTasks,
                pageTasks : newPage,
                totalPagesTasks : newTotalPages
            });
        });
    }

    addCourse(courseId){

        $.post( "/plugins/problems_bank/api/bank_courses", { "course_id": courseId }, (data) => {
            this.updateBankCoursesAsync();
            this.updateAvailableCoursesAsync();
            this.updateTasksAsync();
        }).done((data) => {
            this.setState( {
                dataAlertCourseList:{
                    data: data,
                    isVisibleAlert: true,
                    titleAlert: "Success!",
                    styleAlert: "success"
                }
            });
        }).error((data) => {
            this.setState( {
                dataAlertCourseList: {
                    isVisibleAlert: true,
                    data: {"message": data["responseJSON"]["error"]},
                    titleAlert: "Error!",
                    styleAlert: "danger"
                }
            });
        });
    }

    onAlertTaskListClose(isVisible){
        this.setState({
           dataAlertTaskList: {
               isVisibleAlert: isVisible,
               data: {"message" : ""},
               titleAlert: '',
               styleAlert: ''
           }
        });
    }

    onAlertCourseListClose(isVisible){
        this.setState({
           dataAlertCourseList: {
               isVisibleAlert: isVisible,
               data: {"message" : ""},
               titleAlert: '',
               styleAlert: ''
           }
        });
    }

    addTaskToCourse(targetId, taskId, bankId){
        $.post( "/plugins/problems_bank/api/copy_task",
            {"target_id": targetId, "task_id": taskId, "bank_id": bankId} ,( data ) => {

            this.updateTasksAsync();
        }).done((data) => {
            this.setState( {
                dataAlertTaskList:{
                    data: data,
                    isVisibleAlert: true,
                    titleAlert: "Success!",
                    styleAlert: "success"
                }
            });
        }).error((data) => {
            this.setState( {
                dataAlertTaskList: {
                    isVisibleAlert: true,
                    data: {"message": data["responseJSON"]["error"]},
                    titleAlert: "Error!",
                    styleAlert: "danger"
                }
            });
        });
    };

    setAlertCourseListInvisible(){
        this.setState({
           dataAlertCourseList: {
                data: {"message" : ""},
                isVisibleAlert: false,
                titleAlert: '',
                styleAlert: ''
           }
        });
    }

    setAlertTaskListInvisible(){
        this.setState({
           dataAlertTaskList: {
                data: {"message" : ""},
                isVisibleAlert: false,
                titleAlert: '',
                styleAlert: ''
           }
        });
    }


    onPageTaskChange(page) {
        this.setState({pageTasks: page});
    }

    onPageCourseChange(page) {
        this.setState({pageCourses: page});
    }

    onPageAvailableCourseChange(page) {
        this.setState({pageAvailableCourses: page});
    }

    componentWillMount(){
        this.updateBankCoursesAsync();
        this.updateAvailableCoursesAsync();
        this.updateAvailableCoursesToCopyAsync();
        this.updateTasksAsync();
    }

    render() {
        return (
            <Tabs defaultActiveKey={1} id="bank-page-tabs">
                <Tab eventKey={1} title="Courses">
                    <BankCourseList
                        limit={this.limit}
                        courses={this.state.courses}
                        availableCourses={this.state.availableCourses}
                        page={this.state.pageCourses}
                        totalPages={this.state.totalPagesCourses}
                        pageAvailableCourses={this.state.pageAvailableCourses}
                        totalAvailableCoursePages={this.state.totalPagesAvailableCourses}
                        dataAlert={this.state.dataAlertCourseList}
                        callbackOnChildChangedClose={this.onAlertCourseListClose}
                        callbackUpdateTask={this.updateTasksAsync}
                        callbackUpdateBank={this.updateBankCoursesAsync}
                        callbackUpdateAvailable={this.updateAvailableCoursesAsync}
                        callbackOnPageChange={this.onPageCourseChange}
                        callbackOnPageAvailableCourseChange={this.onPageAvailableCourseChange}
                        callbackOnDeleteCourse={this.deleteCourse}
                        callbackAddCourse={this.addCourse}
                        callbackSetAlertInvisible={this.setAlertCourseListInvisible}
                    />
                </Tab>
                <Tab eventKey={2} title="Tasks">
                    <TaskList
                        tasks={this.state.tasks}
                        limit={this.limit}
                        page={this.state.pageTasks}
                        totalPages={this.state.totalPagesTasks}
                        courses={this.state.availableCoursesToCopy}
                        dataAlert={this.state.dataAlertTaskList}
                        callbackOnChildChangedClose={this.onAlertTaskListClose}
                        callbackOnPageChange={this.onPageTaskChange}
                        callbackUpdateTasks={this.updateTasksAsync}
                        callbackUpdateFilteredTasks={this.updateFilteredTasksAsync}
                        callBackAddTaskToCourse={this.addTaskToCourse}
                        callbackSetAlertInvisible={this.setAlertTaskListInvisible}
                    />
                </Tab>
            </Tabs>
        );
    }
}

export default BankPage;