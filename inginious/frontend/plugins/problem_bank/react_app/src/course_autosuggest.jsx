import React from "react";
import Autosuggest from 'react-autosuggest';
import { Row, Col } from 'react-bootstrap';
import './index.css';

class CourseAutosuggest extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            suggestions: [],
            value: '',
            id: ''
        };
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

    onClick = () => {
        let courseId = this.state.id;
        let callbackOnClick = this.props.callbackOnClick;
        callbackOnClick(courseId);
        this.setState({
            value: '',
            id: ''
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
                <button onClick={this.onClick} className="btn btn-primary">
                    {this.props.messageButton}
                </button>
              </Col>
              <Col mdHidden={6}></Col>
            </Row>
        );
    }
}
export default CourseAutosuggest;
