from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import strawberry
from strawberry.fastapi import GraphQLRouter
from .graphql.schema import Query, Mutation
from .domain.repositories import UnitRepository, TenantRepository, LeaseRepository

# Create repositories for initializing database
unit_repo = UnitRepository()
tenant_repo = TenantRepository()
lease_repo = LeaseRepository()

# Initialize FastAPI app
app = FastAPI(title="FastAPI EventSourcing GraphQL API")

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

# Create a GraphQL route
graphql_app = GraphQLRouter(schema)

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

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
