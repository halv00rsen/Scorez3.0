drop table if exists Beer;
drop table if exists Beer_types;
drop table if exists User;
drop table if exists Score;
create table User (
	username varchar(30) primary key,
	password varchar(30) not null,
	admin boolean not null
);
create table Beer_type(
	name varchar(30) primary key
);
create table Beer (
	name varchar(30) not null,
	type varchar(30) not null,
	primary key (name, type)
);
create table Score (
	id integer primary key autoincrement,
	beer varchar(30) not null,
	type varchar(30) not null,
	user varchar(30) not null,
	p integer not null
);