import React from "react";
import { Modal, Button, Alert } from 'react-bootstrap';

class BankCourse extends React.Component {

    constructor(props, context) {
        super(props, context);

        this.state = {
            showModal: false
        };
    }

    open = () => {
        this.setState({ showModal: true });
    };

    close = () => {
        this.setState({ showModal: false });
    };

    onDeleteCourse = () => {
        let courseId = this.props.name;
        let deleteCourse = this.props.callbackOnDeleteCourse;

        deleteCourse(courseId);

        this.close();
    };

    render() {
        return (
            <div>
                <a type="button" className="list-group-item" >
                    <b>{this.props.name}</b>
                    <span role="button" className="glyphicon glyphicon-remove pull-right text-danger" onClick={this.open}></span>
                </a>
                <Modal className="modal-container"
                    show={this.state.showModal}
                    onHide={this.close}
                    animation={true}
                    bsSize="large">

                    <Modal.Header closeButton>
                        <Modal.Title> {this.props.name} </Modal.Title>
                    </Modal.Header>

                    <Modal.Body>
                      <Alert bsStyle="warning">
                          <h5><strong>Are you sure that you want to remove the bank privileges from this course?</strong></h5>
                          <h6>* The course won't be removed, only the permits to be a bank will be removed.</h6>
                      </Alert>
                    </Modal.Body>

                    <Modal.Footer>
                        <Button onClick={this.close}>Cancel</Button>
                        <Button onClick={this.onDeleteCourse} bsStyle="primary">Remove</Button>
                    </Modal.Footer>
                </Modal>
            </div>
        );
    }
}
export default BankCourse;