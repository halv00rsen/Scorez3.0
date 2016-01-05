drop table if exists Beer;
drop table if exists Beer_type;
drop table if exists User;
drop table if exists Score;
drop table if exists Groupi;
drop table if exists GroupRelation;
drop table if exists FavoriteGroup;
create table User (
	username varchar(30) primary key,
	password varchar(30) not null,
	-- local_admin boolean not null,
	system_admin boolean not null
	-- ,top_group varchar(30)
);
create table Beer_type(
	name varchar(30),
	group_id boolean not null,
	-- group varchar(30),
	-- primary key (name, group)
	primary key (name, group_id)
);
create table Beer (
	name varchar(30) not null,
	type varchar(30) not null,
	group_id integer not null,
	-- group varchar(30) not null,
	-- primary key (name, type, group)
	primary key (name, type, group_id)
);
create table Score (
	id integer primary key autoincrement,
	beer varchar(30) not null,
	type varchar(30) not null,
	user varchar(30) not null,
	-- group varchar(30) not null,
	group_id integer not null,
	p integer not null
);
create table Groupi(
	group_id integer primary key autoincrement,
	name varchar(30) not null,
	owner varchar(30) not null
);
create table GroupRelation(
	-- name varchar(30) not null,
	-- owner varchar(30) not null,
	group_id integer not null,
	user varchar(30) not null,
	del_element boolean,
	types_handling boolean,
	add_points boolean,
	primary key (user, group_id)
	-- primary key (name, owner, user)
);
create table FavoriteGroup(
	username varchar(30) primary key,
	group_id not null
);