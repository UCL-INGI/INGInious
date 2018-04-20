import React from "react";
import { Alert } from 'react-bootstrap';

class CustomAlert extends React.Component {

    handleAlertDismiss = () => {

        let updateParent = this.props.callbackParent;
        updateParent(false);

        this.forceUpdate();
    };

    render() {
        if (this.props.isVisible) {
          return (
            <Alert bsStyle="success" onDismiss={this.handleAlertDismiss}>
              <h4>Success!</h4>
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