#!/usr/bin/perl

#
# HTTP DELETE
#  username
#  session_token
#  tweet_id
#
# On success, returns JSON
#   { "tweet_id" : 5342, "isdeleted" : 1, "tweet" : "[delete]" }
#
# The tweet is not actually deleted from the DB, but the content
# is replaced with "[delete]", the isdeleted column is set to true,
# and the time_stamp is updated so that that any clients will be
# notified that it has been deleted upon refresh.
#
# Errors
#   500 Internal Server Error : my bad
#   400 Bad Request : all parameters not provided
#   401 Unauthorized : username doesn't exist or session_token mismatch
#   403 Forbidden : not the user's tweet.
#   404 Not Found : no such user or no such tweet
#

use strict;
use CGI;
use DBI;
use HTML::Entities;
use JSON;

my $cgi = new CGI;

my $DB = "wsu-twitter.db";
my $TWEETS = "tweets";
my $USERS = "users";

my $dbh = DBI->connect("DBI:SQLite:dbname=$DB", "", "");
unless ($dbh) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "503 Database Unavailable");
    exit 1;
}

my $username = $cgi->param("username");
my $session_token = $cgi->param("session_token");
my $tweet_id = $cgi->param("tweet_id");

unless (defined $username && length($username) > 0 &&
        defined $session_token && length($session_token) > 0 &&
        defined $tweet_id && length($tweet_id) > 0) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "400 Bad Request");
    exit 1;
}

my $query = 
    "SELECT user_id, session_token FROM $USERS WHERE username = ?";
my $sth = $dbh->prepare($query);
$sth->bind_param(1,$username);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}

my $user_id = -1;
my $session_token_db;

my $rows = $sth->fetchall_arrayref();
foreach my $row (@$rows) {  # should be exactly one row
    ($user_id, $session_token_db) = @$row;
}
$sth->finish();

unless ($user_id >= 0) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "404 Not Found");
    exit 1;
}

# XXXX
#my $MAGIC = "1111";
unless (#$session_token eq $MAGIC || 
	$session_token eq $session_token_db) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "401 Unauthorized");
    exit 1;
}

$query = "SELECT user_id FROM $TWEETS WHERE tweet_id = ?";
$sth = $dbh->prepare($query);
$sth->bind_param(1,$tweet_id);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}

my $tweet_user_id = -1;
$rows = $sth->fetchall_arrayref();
foreach my $row (@$rows) {  # should be exactly one row
    $tweet_user_id = $row->[0];
}
$sth->finish();

unless ($tweet_user_id >= 0) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "404 Not Found");
    exit 1;
}

unless (defined($tweet_user_id) && $user_id == $tweet_user_id) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "403 Forbidden");
    exit 1;
}

$query = 
    "UPDATE $TWEETS SET isdeleted = 1, tweet = '[deleted]', " .
    "time_stamp = DATETIME('NOW','LOCALTIME') WHERE tweet_id = ?";
$sth = $dbh->prepare($query);
$sth->bind_param(1,$tweet_id);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}
$sth->finish();

print $cgi->header(-type => "application/json", 
		   -charset => "utf-8");

print encode_json({"tweet_id" => $tweet_id,
		   "isdeleted" => 1,
		   "tweet" => "[deleted]"});

$dbh->disconnect;
