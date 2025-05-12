"""GraphQL queries for the Boulevard API."""

ORDER_DETAILS_QUERY = """
query OrderDetails($locationId: ID!, $query: QueryString) {
  orders(locationId: $locationId, query: $query, first: 100) {
    edges {
      node {
        id
        closedAt
        summary {
          currentSubtotal
        }
        lineGroups {
          lines {
            __typename
            id
            quantity
            currentSubtotal
            currentDiscountAmount
            
            ... on OrderProductLine {
              productId
              name
            }
            ... on OrderServiceLine {
              serviceId
              name
            }
            ... on OrderGratuityLine {
              id
            }
            ... on OrderAccountCreditLine {
              id
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
"""

LOCATIONS_QUERY = """
query Locations {
  locations(first: 100) {
    edges {
      node {
        id
        name
        address {
          line1
          line2
          city
          state
          zip
          country
        }
      }
    }
  }
}
""" 