declare module "react-hot-loader" {
    import * as React from 'react';

    interface AppContainer extends React.ComponentClass<{}> { }
    export const AppContainer: AppContainer;
}
