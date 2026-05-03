--primary key
create table student(
id int  primary key,
name varchar(20),
age int
)
select* from student
insert into student(id,name,age) values (1,'areeha',23)
drop table student

--serial
create table users(
id  serial,
name varchar(20)
)
 select * from users
 insert into users (name) values('areeha')
 drop table users

 --default
 create table employee1(
 id serial,
 name varchar(20),
 location varchar default 'Pakistan'
 )
 select * from employee1
 insert into employee1(name)values ('areeha')

 --unique key
 create table customer(
c_id serial,
name varchar(20),
email varchar(120) unique
)
select *from customer
insert into customer ( name, email) values ('areeha', 'areehanasir1@gmail.com'),('riha','rihamuqaddas@gmail.com')
drop table customer

--forgien key
create table employee2(
emp_id serial,
emp_name varchar(50),
emp_salary int,
dep varchar(50) primary key
)
select *from employee2
insert into employee2(emp_name,emp_salary,dep)values('areeha',200000,'it'),('riha',300000,'hr'),('kainat',400000,'psychology')

create table department1(
dep varchar(30) primary key,
hod varchar (30),
id serial,
FOREIGN KEY (dep) REFERENCES department1(dep)

)
select * from department1
insert into department1(dep,hod) values('it','usman'),('hr','nida'),('psychology','shiza'),('ir','hammad')
drop table department1

CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(50)
);

CREATE TABLE employees (
    emp_id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

--order by
CREATE TABLE employees12 (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    department VARCHAR(50),
    salary INT,
    city VARCHAR(50)
);
select * from employees12
insert into  employees12 (name, department, salary, city) VALUES
('Ali', 'IT', 50000, 'Lahore'),
('Sara', 'HR', 40000, 'Karachi'),
('Ahmed', 'IT', 60000, 'Lahore'),
('Ayesha', 'Finance', 45000, 'Islamabad'),
('Bilal', 'IT', 55000, 'Karachi'),
('Hina', 'HR', 42000, 'Lahore'),
('Usman', 'Finance', 70000, 'Islamabad');
SELECT * FROM employees12
ORDER BY salary DESC;
SELECT DISTINCT city FROM employees12;
SELECT * FROM employees12
LIMIT 3;
drop table employees12
