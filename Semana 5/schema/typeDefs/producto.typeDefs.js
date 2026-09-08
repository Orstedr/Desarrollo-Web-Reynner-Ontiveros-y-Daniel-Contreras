const { gql } = require('apollo-server-express');

const productoTypeDefs = gql`
    type Producto {
        id: ID!
        nombre: String!
        precio: Float!
        stock: Int!
        categoria: Categoria
    }

    input ProductoInput {
        nombre: String!
        precio: Float!
        stock: Int!
        categoriaId: ID!
    }

    extend type Query {
        getProductos: [Producto]
        getProductoById(id: ID!): Producto
        getProductosByCategoria(categoriaId: ID!): [Producto]
    }

    extend type Mutation {
        addProducto(input: ProductoInput): Producto
        updProducto(id: ID!, input: ProductoInput): Producto
        delProducto(id: ID!): Alert
    }
`;

module.exports = productoTypeDefs;
