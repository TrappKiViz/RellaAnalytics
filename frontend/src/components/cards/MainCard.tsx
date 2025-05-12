import React, { forwardRef } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography,
  CardProps,
  useTheme
} from '@mui/material';

interface MainCardProps extends CardProps {
  border?: boolean;
  boxShadow?: boolean;
  contentSX?: object;
  darkTitle?: boolean;
  divider?: boolean;
  elevation?: number;
  secondary?: React.ReactNode;
  shadow?: string;
  sx?: object;
  title?: React.ReactNode;
}

const MainCard = forwardRef<HTMLDivElement, MainCardProps>(
  (
    {
      border = true,
      boxShadow,
      children,
      content = true,
      contentSX = {},
      darkTitle,
      divider = true,
      elevation,
      secondary,
      shadow,
      sx = {},
      title,
      ...others
    },
    ref
  ) => {
    const theme = useTheme();

    return (
      <Card
        elevation={elevation || 0}
        ref={ref}
        {...others}
        sx={{
          border: border ? '1px solid' : 'none',
          borderColor: theme.palette.grey[200],
          ':hover': {
            boxShadow: boxShadow ? shadow || '0 2px 14px 0 rgb(32 40 45 / 8%)' : 'inherit'
          },
          ...sx
        }}
      >
        {/* card header and action */}
        {!title ? null : (
          <>
            <CardHeader
              sx={{ p: 2.5 }}
              title={
                <Typography
                  variant="h5"
                  sx={{ color: darkTitle ? theme.palette.grey[900] : theme.palette.primary.dark }}
                >
                  {title}
                </Typography>
              }
              action={secondary}
            />
            {divider && <Divider />}
          </>
        )}

        {/* card content */}
        {content && (
          <CardContent sx={{ ...contentSX }} className="content">
            {children}
          </CardContent>
        )}
        {!content && children}
      </Card>
    );
  }
);

MainCard.displayName = 'MainCard';
export default MainCard; 