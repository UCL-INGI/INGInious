import React from "react";
import Autosuggest from 'react-autosuggest';
import { Row, Col, Modal, Button, Alert } from 'react-bootstrap';
import './index.css';

class CourseAutosuggest extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            suggestions: [],
            value: '',
            id: '',
            showModal: false,
        };
        this.open = this.open.bind(this);
        this.close = this.close.bind(this);
    }

    getSuggestions = (value) => {
        const normalizedValue = value.toUpperCase();
        return this.props.courses.filter((course) => {
            return course.name.toUpperCase().startsWith(normalizedValue) ||
                course.id.toUpperCase().startsWith(normalizedValue);
        });
    };

    renderSuggestion = (suggestion, {query, isHighlighted}) => {
        return (
            <span>{suggestion.name}</span>
        );
    };

    onChange = (event, { newValue }) => {
        this.setState({
                value: newValue
            });
    };

    open(){
        this.setState({ showModal: true });
    };

    close(){
        this.setState({ showModal: false });
    };

    onClick = () => {
        let courseId = this.state.id;
        let callbackOnClick = this.props.callbackOnClick;
        callbackOnClick(courseId);
        this.setState({
            value: '',
            id: '',
            showModal: false
        });
    };

    getSuggestionValue = (suggestion) => {
        this.setState({
            id: suggestion.id
        });
        return suggestion.name
    };

    render() {
        const inputProps = {
            placeholder: 'Type a course name or course id',
            value: this.state.value,
            onChange: this.onChange
        };

        return (

            <Row>
              <Col md={this.props.mdInput}>
                <Autosuggest
                    suggestions={this.state.suggestions}
                    onSuggestionsFetchRequested={({value}) => this.setState({suggestions: this.getSuggestions(value)})}
                    onSuggestionsClearRequested={() => this.setState({suggestions: []}) }
                    getSuggestionValue={this.getSuggestionValue}
                    renderSuggestion={this.renderSuggestion}
                    inputProps={inputProps}
                />
              </Col>
              <Col md={this.props.mdButton}>
                <button onClick={this.open} className="btn btn-primary">
                    {this.props.messageButton}
                </button>
              </Col>
              <Modal className="modal-container"
                     show={this.state.showModal}
                           onHide={this.close}
                           animation={true}
                           bsSize="short">

                     <Modal.Header closeButton>
                        <Modal.Title> {this.state.value} </Modal.Title>
                     </Modal.Header>

                     <Modal.Body>
                        <Alert bsStyle="warning">
                            <h5><strong>Are you sure that you want to add this course to the bank?</strong></h5>
                            <h5>
                                * The course and tasks from this course will be public and every user could copy
                                tasks from this course.
                            </h5>
                        </Alert>
                     </Modal.Body>

                     <Modal.Footer>
                        <Button onClick={this.close}>Cancel</Button>
                        <Button onClick={this.onClick} bsStyle="primary">Accept</Button>
                     </Modal.Footer>
              </Modal>
              <Col mdHidden={6}/>
            </Row>
        );
    }
}
export default CourseAutosuggest;
