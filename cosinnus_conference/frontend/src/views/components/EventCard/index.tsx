import React from "react"
import {FormattedMessage} from "react-intl"
import {Card, CardActionArea, CardContent, Typography} from "@material-ui/core"
import clsx from "clsx"

import {Event} from "../../../stores/events/models"
import {formatTime} from "../../../utils/events"
import {useStyles} from "./style"
import {ManageEventIcons} from "../ManageEventIcons"

export interface EventCardProps {
  event: Event
}

export function EventCard(props: EventCardProps) {
  const { event } = props
  const classes = useStyles()
  if (!event) {
    return null
  }
  const isNow = event.isNow()
  return (
    <Card className={clsx({
      [classes.card]: true,
      [classes.break]: event.props.isBreak,
    })}>
      <CardActionArea
        classes={{
          root: classes.actionArea,
          focusHighlight: classes.focusHighlight
        }}
        onClick={() => {
          const url = event.getUrl()
          if (url) window.location.href = url
        }}
      >
        <CardContent>
          <div className={classes.left}>
            {isNow && (
              <Typography component="span">
                <FormattedMessage id="Now" defaultMessage="Now" />
                {"-" + formatTime(event.props.toDate)}
              </Typography>
            ) || (
              <Typography component="span">
                {formatTime(event.props.fromDate) + "-" + formatTime(event.props.toDate)}
              </Typography>
            )}
            <Typography component="span">
              {event.props.title}
            </Typography>
            <Typography component="p">
              {event.getNoteOrPresenters()}
            </Typography>
          </div>
          <div className={classes.right}>
            {isNow && (
              <div>
                <Typography component="span">
                  {event.getMinutesLeft()}&nbsp;
                  <FormattedMessage id="minutes left" defaultMessage="minutes left" />
                </Typography>
                <Typography component="p">
                  {event.props.participantsCount}&nbsp;
                  <FormattedMessage id="participants" defaultMessage="participants" />
                </Typography>
                <Typography component="p"> </Typography>
              </div>
            ) || (
              <div>
                {/*
                <Link href="#" className={classes.link}>
                  <FontAwesomeIcon icon={faUserPlus} />
                </Link>
                <Link href="#" className={classes.link}>
                  <FontAwesomeIcon icon={faHeart} />
                </Link>
                <Link href="#" className={classes.link}>
                  <FontAwesomeIcon icon={faCalendarPlus} />
                </Link>
                */}
              </div>
            )}
          </div>
          <ManageEventIcons event={event} />
        </CardContent>
      </CardActionArea>
    </Card>
  )
}
