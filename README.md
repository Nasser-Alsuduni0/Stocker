# Stocker

## Using Django create a website for managing corporate inventory !
The project name is `Iventory Plus` . A comprehensive system to manage inventory and stock of a corporate.

## Features List

### Product Management
- Add new products
- Edit product details
- Delete products
- View products list
- View product details.
- Stock Management (Update stock levels, view stock status)
- Search products


### Category Management
- Add new categories
- Edit category details
- Delete categories
- View categories list


### Supplier Management
- Add new suppliers
- Edit supplier details
- Delete suppliers
- View suppliers list
- View supplier details.



### Reports and Analytics
- Generate inventory reports
- Generate supplier reports

### Notifications 
(using email to send to manager's email)
- Low stock alerts
- Expiry date alerts for perishable items


### Import/Export Data (Bonus)
- Import product data from CSV
- Export inventory data to CSV


## Requirements

### Functional Requirements

- The system must allow the addition, modification, and deletion of products, categories, and suppliers.
- The system must provide search functionality for products, and suppliers.
- The system must track stock levels and allow updating of stock quantities.
- The system must generate and display various reports related to inventory.
- The system must send notifications for low stock and approaching expiry dates (using email to send to manager's email).
- The system must allow importing and exporting data in CSV format (Bonus).


### Non-Functional Requirements

- The system should be responsive and work on various devices.
- The system should have a user-friendly interface.
- The system should handle concurrent users without performance degradation.
- The system should ensure data security and integrity.
- The system should provide detailed error messages and logging for debugging purposes.



## User Stories

### Product Management

- As an Inventory Manager, I want to add new products so that I can keep the inventory up to date.
- As an Inventory Manager, I want to edit product details so that I can correct any mistakes or update information.
- As an Inventory Manager, I want to delete products that are no longer available so that the inventory list is accurate.
- As an Inventory Manager, I want to view a list of all products so that I can easily manage the inventory.
- As an Inventory Manager, I want to search for products by name, category, or supplier so that I can quickly find specific items.


### Category Management

- As an Inventory Manager, I want to add new categories so that I can organize products better.
- As an Inventory Manager, I want to edit category details so that I can update category information.
- As an Inventory Manager, I want to delete categories that are no longer needed so that the category list remains relevant.
- As an Inventory Manager, I want to view a list of all categories so that I can see how products are organized.


### Supplier Management

- As an Inventory Manager, I want to add new suppliers so that I can track where products are sourced.
- As an Inventory Manager, I want to edit supplier details (name, logo, email, website, phone number, etc.) so that I can update their contact information.
- As an Inventory Manager, I want to delete suppliers that we no longer work with so that the supplier list is current.
- As an Inventory Manager, I want to view a list of all suppliers so that I can manage supplier relationships.
Stock Management
- As an Inventory Manager, I want to view a list of all inventory supplied by a supplier so that I can track how much business we do with the supplier.


### Stock Management

- As an Inventory Manager, I want to update stock levels for a product so that the inventory quantities are accurate.
- As an Inventory Manager, I want to view stock status so that I can identify which products need restocking.
- As an Inventory Manager, I want to generate stock reports so that I can review inventory trends and make informed decisions.


### Reports and Analytics

- As an Inventory Manager, I want to view inventory reports so that I can review the overall inventory status.
- As an Inventory Manager, I want to view supplier reports so that I can evaluate supplier performance.
- As an Inventory Manager, I want to receive low stock alerts so that I can reorder products before they run out.
- As an Inventory Manager, I want to receive expiry date alerts for perishable items so that I can manage them before they expire.
Import/Export Data


- (Bonus) As an Inventory Manager, I want to import product data from CSV files so that I can quickly add multiple products to the system.
As an Inventory Manager, I want to export inventory data to CSV files so that I can share it with others or analyze it in external tools.



### Models:
- Product.
- Category.
- Supplier

#### Relationships
- A product belongs to one category.
- A product can be supplied by multiple suppliers.

### Users & Permissions
- You have two types of users : normal user (employee) and admin user.
- Normal user can view/update stock, view/add/update product. But cannot delete product. Cannot add/update/delete categories/suppliers.
- Admin has all the permissions. Can view/add/update/delete products, categories, suppliers. 


## To be provided by you
- **UML:** [View UML](./docs/Stocker_UML.png)
- **Wireframe:** [View Wireframe](./docs/Stock-Wireframe.pdf)
## Note:
- use best practices.
- take good care of user experience (feedback, pagination, etc.)

      
## Resources:

**Free high quality images :**

- https://www.pexels.com/
- https://unsplash.com

**Free sounds website:**

- https://mixkit.co/

**Free stock videos:**

- https://pixabay.com/videos/

**Free Fonts:**

- https://fonts.google.com

**Free Icons**

- https://fonts.google.com/icons
- https://icons.getbootstrap.com/

**CSS Library:**

- https://getbootstrap.com/
- https://get.foundation/index.html

**CSS Animation libraries:**

- https://animate.style
- https://www.minimamente.com/project/magic/


## Use python-dotenv to save your sensitive data.
- https://pypi.org/project/python-dotenv/


## Use a CDN or cloud storage provider to sore your large static files (videos, images, etc.), such as:
- https://firebase.google.com/docs/storage


## Use Git & Github to manage and track changes in your project.
- At lease commit and sync the changes once at the end of everyday.


## Edit the README.md file to include (include the info at the top):
- UML link.
- wireframe link.

## Wireframe / Design tools
- https://www.figma.com/templates/wireframe-kits/
- https://www.mockflow.com/

## UML design tools
- https://www.lucidchart.com/pages/examples/uml_diagram_tool
- https://app.diagrams.net/
