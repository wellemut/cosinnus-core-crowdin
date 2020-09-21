import React, {useState} from "react"
import {Button} from "@material-ui/core"
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome"
import {faPen, faPlus, faTrashAlt} from "@fortawesome/free-solid-svg-icons"
import {FormattedMessage} from "react-intl"

import {Event} from "../../../stores/events/models"
import {useStyles} from "./style"

interface ManageEventButtonsProps {
  event: Event
}

export function ManageEventButtons(props: ManageEventButtonsProps) {
  const {event} = props
  const classes = useStyles()
  if (!event.props.managementUrls) {
    return null
  }
  return (
    <div className={classes.buttons}>
      {event.props.managementUrls.updateEvent && (
        <Button
          variant="contained"
          disableElevation
          href="#"
          onClick={() => window.location.href = event.props.managementUrls.updateEvent}
        >
          <FontAwesomeIcon icon={faPen} />&nbsp;
          <FormattedMessage id="Edit event" defaultMessage="Edit event" />
        </Button>
      )}
      {event.props.managementUrls.deleteEvent && (
        <Button
          variant="contained"
          disableElevation
          href="#"
          onClick={() => window.location.href = event.props.managementUrls.deleteEvent}
        >
          <FontAwesomeIcon icon={faTrashAlt} />&nbsp;
          <FormattedMessage id="Delete event" defaultMessage="Delete event" />
        </Button>
      )}
    </div>
  )
}
