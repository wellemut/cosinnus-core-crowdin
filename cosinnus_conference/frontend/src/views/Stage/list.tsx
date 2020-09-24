import {
  Grid, ListItem, ListItemText,
  Typography
} from "@material-ui/core"
import React, {useEffect, useState} from "react"
import {connect as reduxConnect} from "react-redux"
import {RouteComponentProps} from "react-router-dom"
import {withRouter} from "react-router"
import {FormattedMessage} from "react-intl";

import {RootState} from "../../stores/rootReducer"
import {fetchEvents} from "../../stores/events/effects"
import {DispatchedReduxThunkActionCreator} from "../../utils/types"
import {Event} from "../../stores/events/models"
import {Content} from "../components/Content/style"
import {EventList} from "../components/EventList"
import {Sidebar} from "../components/Sidebar"
import {ManageRoomButtons} from "../components/ManageRoomButtons"
import {Room} from "../../stores/room/models"

interface StageProps {
  events: Event[]
  fetchEvents: DispatchedReduxThunkActionCreator<Promise<void>>
  room: Room
}

function mapStateToProps(state: RootState) {
  return {
    events: state.events[state.room.props.id],
    room: state.room,
  }
}

const mapDispatchToProps = {
  fetchEvents: fetchEvents
}

function StageConnector (props: StageProps & RouteComponentProps) {
  const { events, fetchEvents, room } = props
  // Rerender every minute
  const [time, setTime] = useState(new Date())
  useEffect(() => { setInterval(() => setTime(new Date()), 60000) })

  if (!events) {
    fetchEvents()
  }
  return (
    <Grid container>
      <Content>
        <Typography component="h1"><FormattedMessage id="Agenda" /></Typography>
        {room.props.descriptionHtml && (
          <div className="description" dangerouslySetInnerHTML={{__html: room.props.descriptionHtml}} />
        )}
        {events && events.length > 0 && (
          <EventList events={events} />
        ) || <Typography><FormattedMessage id="No stage events." /></Typography>
        }
        <ManageRoomButtons />
      </Content>
      {room.props.url && <Sidebar url={room.props.url} />}
    </Grid>
  )
}

export const Stage = reduxConnect(mapStateToProps, mapDispatchToProps)(
  withRouter(StageConnector)
)
