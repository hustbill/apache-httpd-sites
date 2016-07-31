#!/usr/bin/perl -wT

#
# HTTP POST
#  username
#  session_token
#  tweet
#
# On success it simply echoes back tweet via JSON object:
#   {"tweet" : "content of tweet"}
#
# Note: Since there is no way to know what the tweet_id or actual
#   time date stamp is after it was added, the client should fetch
#   new tweets (tweets later than its latest stored time stamp).
#
# Note: By default autocommit is on (we could turn it off
#    $dbh->{AutoCommit} = 0;) so there is no need for
#    $dbh->commit; statements.
#
# Errors
#   500 Internal Server Error : my bad
#   400 Bad Request : all parameters not provided
#   401 Unauthorized : session_token mismatch
#   404 Not Found : no such user
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
my $tweet = $cgi->param("tweet");

unless (defined $username && length($username) > 0 &&
        defined $session_token && length($session_token) > 0 &&
        defined $tweet && length($tweet) > 0) {
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

$sth = $dbh->prepare("INSERT INTO $TWEETS (user_id, tweet) VALUES(?, ?)");
$sth->bind_param(1,$user_id);
$sth->bind_param(2,$tweet);
unless (defined $sth->execute()) {
    print $cgi->header(-type => "application/json", 
		       -charset => "utf-8",
		       -status => "500 Internal Server Error");
    exit 1;
}
$sth->finish();

print $cgi->header(-type => "application/json", 
		   -charset => "utf-8");

print encode_json({"tweet" => $tweet});

$dbh->disconnect;
