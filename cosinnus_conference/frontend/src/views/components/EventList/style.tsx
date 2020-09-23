import { makeStyles } from '@material-ui/core/styles';

export const useStyles = makeStyles((theme) => ({
  list: {
    "& li": {
      "&:first-child": {
        background: "transparent",
        padding: 0,
        "& span": {
          fontWeight: 700,
          textTransform: "uppercase"
        },
      }
    },
    "& > div": {
      background: theme.palette.background.paper,
      height: "3rem",
      borderRadius: ".3rem",
      marginBottom: "1rem",
      padding: 0,
      "& div:first-child": {
        "& span, & p": {
          color: theme.palette.text.secondary
        }
      },
      "& div": {
        "& span": {
          fontWeight: 700,
          lineHeight: "1.3",
        },
        "& p": {
          background: "transparent",
          color: theme.palette.text.secondary,
          padding: 0,
          lineHeight: "1.3",
        }
      },
      "&:hover": {
        background: theme.palette.primary.main,
        "& div:first-child": {
          "& span, & p": {
            color: theme.palette.primary.light
          }
        },
        "& div": {
          "& span": {
            color: "#ffffff"
          },
          "& p": {
            color: theme.palette.primary.light,
          }
        }
      },
      [theme.breakpoints.down('sm')]: {
        height: "auto",
        padding: "1rem",
      },
    },
    "& > li, & > div": {
      [theme.breakpoints.down('sm')]: {
        flexWrap: "wrap",
      },
      "& div:first-child": {
        flexBasis: "20%",
        "& span, & p": {
          textAlign: "right",
          textTransform: "uppercase",
          fontWeight: 700,
          paddingRight: "1.5rem",
          [theme.breakpoints.down('sm')]: {
            textAlign: "left",
          },
        },
        [theme.breakpoints.down('sm')]: {
          flexBasis: "100%",
        },
      },
      "& div": {
        flexBasis: "80%",
        margin: "0.2rem",
        [theme.breakpoints.down('sm')]: {
          flexBasis: "100%",
        },
      },
    },
    "&.now > div": {
      background: theme.palette.primary.contrastText,
    },
  }
}))
