import { useLocation, useNavigate, useParams } from 'react-router-dom';

export function withRouter(Component: any) {
    return function Wrapper(props: any) {
        const params = useParams();
        const navigate = useNavigate();
        const location = useLocation();

        return <Component {...props}
            navigate={navigate}
            params={params}
            location={location}
        />;
    };
}
