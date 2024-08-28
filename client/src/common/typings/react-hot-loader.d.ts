declare module "react-hot-loader" {
    import React from 'react';

    interface AppContainer extends React.ComponentClass<{}> { }
    export const AppContainer: AppContainer;
}
