drop table if exists Beer;
drop table if exists Beer_type;
drop table if exists User;
drop table if exists Score;
drop table if exists Groupi;
drop table if exists GroupRelation;
create table User (
	username varchar(30) primary key,
	password varchar(30) not null,
	local_admin boolean not null,
	system_admin boolean not null
);
create table Beer_type(
	name varchar(30),
	-- group varchar(30),
	-- primary key (name, group)
	primary key (name)
);
create table Beer (
	name varchar(30) not null,
	type varchar(30) not null,
	-- group varchar(30) not null,
	-- primary key (name, type, group)
	primary key (name, type)
);
create table Score (
	id integer primary key autoincrement,
	beer varchar(30) not null,
	type varchar(30) not null,
	user varchar(30) not null,
	-- group varchar(30) not null,
	p integer not null
);
create table Groupi(
	-- id integer primary key autoincrement,
	name varchar(30) not null,
	owner varchar(30) not null,
	primary key (name, owner)
);
create table GroupRelation(
	name varchar(30) not null,
	owner varchar(30) not null,
	user varchar(30) not null,
	primary key (name, owner, user)
);