from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
from .graphql.schema import Query, Mutation
from .domain.repositories import UnitRepository, TenantRepository, LeaseRepository

# Application state
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize repositories
    app_state["unit_repo"] = UnitRepository()
    app_state["tenant_repo"] = TenantRepository()
    app_state["lease_repo"] = LeaseRepository()

    yield

    # Clean up repositories
    app_state["unit_repo"].close()
    app_state["tenant_repo"].close()
    app_state["lease_repo"].close()


# Initialize FastAPI app with lifespan management
app = FastAPI(title="FastAPI EventSourcing GraphQL API", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create GraphQL schema with Strawberry
schema = strawberry.Schema(query=Query, mutation=Mutation)


# Create a GraphQL route with custom context
async def get_context():
    # Use repositories from app state
    return {
        "unit_repo": app_state["unit_repo"],
        "tenant_repo": app_state["tenant_repo"],
        "lease_repo": app_state["lease_repo"],
    }


graphql_app = GraphQLRouter(schema, context_getter=get_context)

# Add the GraphQL routes to the FastAPI application
app.include_router(graphql_app, prefix="/graphql")


# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/")
def root():
    return {
        "message": "Welcome to FastAPI EventSourcing GraphQL API. Visit /graphql for the GraphQL playground."
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
