import React from "react";
import Autosuggest from 'react-autosuggest';
import SweetAlert from 'react-bootstrap-sweetalert';
import { Row, Col } from 'react-bootstrap';
import './index.css';

class CourseAutosuggest extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            suggestions: [],
            value: '',
            selectedCourse: {
                id: '',
                name: ''
            },
            show: false,
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
        this.setState({ show: true });
    };

    close(){
        this.setState({ show: false });
    };

    onConfirm = () => {
        let courseId = "";
        if(this.state.selectedCourse.name.toUpperCase() === this.state.value.toUpperCase()){
            courseId = this.state.selectedCourse.id;
        }
        let callbackOnClick = this.props.callbackOnClick;
        callbackOnClick(courseId);
        this.setState({
            value: '',
            selectedCourse: {
                id: '',
                name: ''
            },
            show: false
        });
    };

    getSuggestionValue = (suggestion) => {
        this.setState({
            selectedCourse: suggestion
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
                <button onClick={this.open} className="btn btn-primary" disabled={!this.state.value}>
                    {this.props.messageButton}
                </button>
              </Col>
              <SweetAlert
                  warning
                  showCancel
                  confirmBtnText={"Yes!"}
                  confirmBtnBsStyle={"warning"}
                  cancelBtnBsStyle={"danger"}
                  show={this.state.show}
                  title={this.props.alertTitle}
                  onConfirm={this.onConfirm}
                  onCancel={this.close}
              >
                  {this.props.alertText}
              </SweetAlert>
              <Col mdHidden={6}/>
            </Row>
        );
    }
}
export default CourseAutosuggest;
