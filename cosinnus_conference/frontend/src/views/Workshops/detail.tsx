import {
  Grid,
  Typography
} from "@material-ui/core"
import React from "react"
import {connect as reduxConnect} from "react-redux"
import {RouteComponentProps} from "react-router-dom"
import {withRouter} from "react-router"
import {FormattedMessage} from "react-intl";
import Iframe from "react-iframe"

import {RootState} from "../../stores/rootReducer"
import {DispatchedReduxThunkActionCreator} from "../../utils/types"
import {EventSlot} from "../../stores/events/models"
import {useStyles as iframeUseStyles} from "../components/Iframe/style"
import {Content} from "../components/Content/style"
import {Sidebar} from "../components/Sidebar"
import {fetchWorkshops} from "../../stores/workshops/effects"
import {useStyles} from "./style"
import {EventCard} from "../components/EventCard"
import {Main} from "../components/Main/style"
import {Loading} from "../components/Loading"
import {fetchEvents} from "../../stores/events/effects"
import {findEventById} from "../../utils/events"
import {ManageEventButtons} from "../components/ManageEventButtons"
import {IframeContent} from "../components/IframeContent"

interface WorkshopProps {
  id: number
  events: EventSlot[]
  fetchEvents: DispatchedReduxThunkActionCreator<Promise<void>>
}

function mapStateToProps(state: RootState) {
  return {
    events: state.events[state.room.props.id],
  }
}

const mapDispatchToProps = {
  fetchEvents
}

function WorkshopConnector (props: WorkshopProps & RouteComponentProps) {
  const { id, events, fetchEvents } = props
  const classes = useStyles()
  const iframeClasses = iframeUseStyles()
  let event = null
  if (events) {
    event = findEventById(events, id)
  } else {
    fetchEvents()
  }
  return (
    <Main container>
      {event && (
        <Content>
          <Typography component="h1">{event.props.title}</Typography>
          {event.props.note && <Typography component="p">{event.props.note}</Typography>}
          <IframeContent url={event.props.url} />
          <ManageEventButtons event={event} />
        </Content>
      ) || (
        <Content>
          <Loading />
        </Content>
      )}
    </Main>
  )
}

export const Workshop = reduxConnect(mapStateToProps, mapDispatchToProps)(
  withRouter(WorkshopConnector)
)
