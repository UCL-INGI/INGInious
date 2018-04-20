import React from "react";
import { Well } from 'react-bootstrap';
import './index.css';

import UltimatePagination from './ultimate_pagination';
import BankCourse from './bank_course'
import CourseAutosuggest from './course_autosuggest'

class BankCourseList extends React.Component {

    render() {
        let courses = this.props.courses.map((course, i) => {
            if(i >= ((this.props.page - 1) * this.props.limit) && i < (this.props.page * this.props.limit)) {
                return (
                    <BankCourse
                        name={course}
                        key={i}
                        callbackOnDeleteCourse={this.props.callbackOnDeleteCourse}
                    />
                )
            }
        });

        return (
            <div>

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

                <div>The following courses are marked as task sources: </div>

                <div className="list-group">{courses}</div>

                <UltimatePagination
                     currentPage={this.props.page}
                     totalPages={this.props.totalPages}
                     onChange={this.props.callbackOnPageChange}
                />

            </div>

        );
    }
}

export default BankCourseList;