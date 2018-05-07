import React from "react";
import { Well, Row, Col } from 'react-bootstrap';
import './index.css';

import UltimatePagination from './ultimate_pagination';
import BankCourse from './bank_course'
import CourseAutosuggest from './course_autosuggest'
import CustomAlert from './custom_alert';

class BankCourseList extends React.Component {

    render() {
        let courses = this.props.courses.map((course, i) => {
            if(i >= ((this.props.page - 1) * this.props.limit) && i < (this.props.page * this.props.limit)) {
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

        let listGroupCoursesContent = courses.length ? courses : "There are no available courses";
        
        let availableCourses = this.props.availableCourses.map((course, i) => {
            if(i >= ((this.props.pageAvailableCourses - 1) * this.props.limit) &&
                i < (this.props.pageAvailableCourses * this.props.limit)) {
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

                        <div className="list-group">{listGroupCoursesContent}</div>

                        <UltimatePagination
                             currentPage={this.props.page}
                             totalPages={this.props.totalPages}
                             onChange={this.props.callbackOnPageChange}
                        />
                    </Col>
                    <Col md={6}>
                        <div>
                            The following are courses which you are admin and are not marked as bank:
                            <br/>
                            <small> (You can copy tasks from these courses to other courses which you are admin)</small>
                        </div>

                        <div className="list-group">{availableCourses}</div>

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