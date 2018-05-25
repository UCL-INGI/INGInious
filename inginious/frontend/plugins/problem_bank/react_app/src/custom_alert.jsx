import React from "react";
import { Alert } from 'react-bootstrap';

class CustomAlert extends React.Component {
    constructor(props){
        super(props);
        this.timer = 0;
        this.handleDelayedDismiss = this.handleDelayedDismiss.bind(this);
        this.handleAlertDismiss = this.handleAlertDismiss.bind(this);
    }

    handleAlertDismiss(){
        clearTimeout(this.timer);
        let updateParent = this.props.callbackParent;
        updateParent(false);

        this.forceUpdate();
    }

    handleDelayedDismiss(){
        this.timer = setTimeout(this.props.callbackSetAlertInvisible, 10000)
    }

    render() {
        if (this.props.isVisible) {
          clearTimeout(this.timer);
          this.handleDelayedDismiss();
          return (
            <Alert bsStyle={this.props.styleAlert} onDismiss={this.handleAlertDismiss}>
              <h4>{this.props.titleAlert}</h4>
              <p>{this.props.message}</p>
            </Alert>
          );
        }else{
            return (
                <p>
                </p>
            );
        }
    }
}

export default CustomAlert;