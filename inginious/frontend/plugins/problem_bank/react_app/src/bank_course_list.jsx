import React from "react";
import { Well, Row, Col } from 'react-bootstrap';
import './index.css';

import UltimatePagination from './ultimate_pagination';
import BankCourse from './bank_course'
import CourseAutosuggest from './course_autosuggest'
import CustomAlert from './custom_alert';

class BankCourseList extends React.Component {

    getListOfCourses = () => {
        let courses = this.props.courses.map((course, i) => {
            let page = this.props.page;
            let limit = this.props.limit;
            let courseIsInBoundsOfPage = i >= ((page - 1) * limit) && i < (page * limit);

            if(courseIsInBoundsOfPage) {
                return (
                    <BankCourse
                        name={course.name}
                        removable={course.is_removable}
                        id={course.id}
                        key={i}
                        callbackOnDeleteCourse={this.props.callbackOnDeleteCourse}
                    />
                )
            }
        });

        if(!courses.length){
            courses = "There are no available courses";
        }
        return courses;
    };

    getListOfAvailableCourses = () => {
        let availableCourses = this.props.availableCourses.map((course, i) => {
            let page = this.props.pageAvailableCourses;
            let limit = this.props.limit;
            let courseIsInBoundsOfPage = i >= ((page - 1) * limit) && i < (page * limit);

            if(courseIsInBoundsOfPage) {
                return (
                    <BankCourse
                        name={course.name}
                        removable={false}
                        id={course.id}
                        key={i}
                        callbackOnDeleteCourse={this.props.callbackOnDeleteCourse}
                    />
                )
            }
        });

        if(!availableCourses.length){
            availableCourses = "There are no available courses";
        }
        return availableCourses;
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
                <Well bsSize="small">
                    <h5>Select course to become in bank</h5>
                    <CourseAutosuggest
                        courses={this.props.availableCourses}
                        alertTitle={"Are you sure you want to add this course to the bank?"}
                        alertText={"* The course and tasks from this course will be public and every user could copy"}
                        callbackOnClick={this.props.callbackAddCourse}
                        messageButton={"Add course to bank"}
                        mdInput={3}
                        mdButton={2}
                    />
                </Well>

                <Row>
                    <Col md={6}>
                        <div>
                            The following courses are marked as task sources:
                            <br/>
                            <small> (You are free to copy the tasks from these courses) </small>
                        </div>

                        <div className="list-group">{this.getListOfCourses()}</div>

                        <UltimatePagination
                             currentPage={this.props.page}
                             totalPages={this.props.totalPages}
                             onChange={this.props.callbackOnPageChange}
                        />
                    </Col>
                    <Col md={6}>
                        <div>
                            The following courses are not marked as bank and you are admin:
                            <br/>
                            <small> (You can copy tasks from these courses to other courses which you are admin)</small>
                        </div>

                        <div className="list-group">{this.getListOfAvailableCourses()}</div>

                        <UltimatePagination
                             currentPage={this.props.pageAvailableCourses}
                             totalPages={this.props.totalAvailableCoursePages}
                             onChange={this.props.callbackOnPageAvailableCourseChange}
                        />
                    </Col>
                </Row>
            </div>

        );
    }
}

export default BankCourseList;